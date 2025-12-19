from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # ... other admin panel URLs may be here ...

    # This path ensures the report URL maps to the correct, fixed view.
    path('reports/share-value-trends/', views.share_value_trends_data, name='share_value_trends_data'),

    # ... other admin panel URLs may be here ...
]