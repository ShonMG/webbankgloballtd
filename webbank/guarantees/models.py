from django.db import models
from accounts.models import User
from loans.models import Loan

class Guarantee(models.Model):
    GUARANTEE_STATUS = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('released', 'Released'),
        ('called', 'Called'),
        ('rejected', 'Rejected'),
    )
    
    guarantor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guarantees_given')
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='guarantees')
    amount_guaranteed = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=GUARANTEE_STATUS, default='pending')
    guarantee_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.guarantor.username} guarantees {self.loan.loan_id}"