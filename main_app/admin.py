from django.contrib import admin

from .models import ModeUnlock, Transaction, Category, Budget, Calendar

admin.site.register(ModeUnlock)
admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(Budget)
admin.site.register(Calendar)


