from apps.accounts.models import User

class SuperAdminService:
    def get_all_superadmins(self):
        return User.objects.filter(role="super_admin").values(
            'id',
            'email',
            'name', 
            'role', 
            'is_active', 
            'is_approved', 
            'date_joined',  
            'region',
            'payment'
        )
    
    def super_admin_approval(self):
        return User.objects.filter(role="super_admin").values('payment').update(True)