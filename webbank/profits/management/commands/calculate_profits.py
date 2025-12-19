from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from profits.models import ProfitCycle, MemberProfit
from members_amor108.models import Member as Amor108Member
from shares.models import Share, ShareTransaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Calculates profits for a given cycle and allocates them to members proportional to their shares.'

    def add_arguments(self, parser):
        parser.add_argument('--cycle-name', type=str, help='Name of the profit cycle (e.g., "Q1 2025").')
        parser.add_argument('--start-date', type=str, help='Start date of the profit cycle (YYYY-MM-DD).')
        parser.add_argument('--end-date', type=str, help='End date of the profit cycle (YYYY-MM-DD).')
        parser.add_argument('--total-profit', type=Decimal, help='Total profit generated for this cycle (e.g., 100000.00).')
        parser.add_argument('--tax-rate', type=Decimal, default=Decimal('0.05'), help='Default tax rate for profit distribution (e.g., 0.05 for 5%).')


    def handle(self, *args, **options):
        cycle_name = options['cycle_name']
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        total_profit_generated = options['total_profit']
        tax_rate = options['tax_rate']

        if not all([cycle_name, start_date_str, end_date_str, total_profit_generated]):
            self.stderr.write(self.style.ERROR('Missing required arguments: --cycle-name, --start-date, --end-date, --total-profit'))
            return

        try:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            self.stderr.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD.'))
            return
        
        if total_profit_generated <= 0:
            self.stderr.write(self.style.ERROR('Total profit generated must be a positive value.'))
            return

        with transaction.atomic():
            # 1. Create a new ProfitCycle
            profit_cycle, created = ProfitCycle.objects.get_or_create(
                name=cycle_name,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    'total_profit_generated': total_profit_generated,
                    'status': 'CALCULATED',
                    'distributed_by': None, # Will be set during distribution
                }
            )

            if not created and profit_cycle.status != 'PENDING':
                self.stderr.write(self.style.WARNING(f"Profit Cycle '{cycle_name}' already exists and is not PENDING. Status: {profit_cycle.status}. Skipping calculation."))
                return
            
            self.stdout.write(self.style.SUCCESS(f"Processing Profit Cycle: {profit_cycle.name}"))

            # 2. Get all active Amor108Members with shares
            # We need to consider shares held during the profit cycle.
            # For simplicity, we'll use current shares. A more complex system
            # would track historical share ownership.
            members_with_shares = Amor108Member.objects.filter(share_account__units__gt=0).select_related('share_account', 'user')
            
            if not members_with_shares.exists():
                self.stdout.write(self.style.WARNING("No members with shares found to allocate profits to."))
                profit_cycle.status = 'CLOSED' # Or 'NO_MEMBERS'
                profit_cycle.save()
                return

            # Calculate total units across all eligible members
            total_units_across_members = members_with_shares.aggregate(total_units=Sum('share_account__units'))['total_units']
            
            if not total_units_across_members or total_units_across_members == 0:
                self.stdout.write(self.style.WARNING("Total units across members is zero. Cannot allocate profits."))
                profit_cycle.status = 'CLOSED' # Or 'NO_SHARES'
                profit_cycle.save()
                return

            total_allocated_profit_sum = Decimal('0.00')

            # 3. Allocate profit to each member proportional to their shares
            for member in members_with_shares:
                share_units = member.share_account.units
                
                if share_units > 0:
                    proportion = Decimal(share_units) / Decimal(total_units_across_members)
                    allocated_profit = (total_profit_generated * proportion).quantize(Decimal('0.01'))
                    
                    tax = (allocated_profit * tax_rate).quantize(Decimal('0.01'))
                    net_profit = (allocated_profit - tax).quantize(Decimal('0.01'))

                    MemberProfit.objects.create(
                        profit_cycle=profit_cycle,
                        member=member,
                        allocated_profit=allocated_profit,
                        tax_amount=tax,
                        net_profit=net_profit,
                        action='PENDING' # Member needs to choose to withdraw or reinvest
                    )
                    total_allocated_profit_sum += net_profit
                    self.stdout.write(self.style.MIGRATE_SUCCESS(f"Allocated {net_profit} to {member.user.username} (Shares: {share_units})"))
                
            profit_cycle.total_distributed_profit = total_allocated_profit_sum
            profit_cycle.status = 'CALCULATED'
            profit_cycle.save()
            
            self.stdout.write(self.style.SUCCESS(f"Profit calculation for '{profit_cycle.name}' completed. Total profit generated: {total_profit_generated}, Total net distributed: {total_allocated_profit_sum}"))

