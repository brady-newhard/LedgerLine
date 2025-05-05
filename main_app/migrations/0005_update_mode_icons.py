from django.db import migrations

def update_mode_icons(apps, schema_editor):
    ModeUnlock = apps.get_model('main_app', 'ModeUnlock')
    
    # Define icon mapping
    mode_icons = {
        'Lockdown Mode': '🔒',
        'Vacay Mode': '🏝️',
        'Survival Mode': '⚠️',
        'Stability Mode': '🏆',
        'Saver Mode': '💰'
    }
    
    # Update existing modes with their icons
    for mode in ModeUnlock.objects.all():
        if mode.name in mode_icons:
            mode.icon = mode_icons[mode.name]
            mode.save()

def reverse_mode_icons(apps, schema_editor):
    ModeUnlock = apps.get_model('main_app', 'ModeUnlock')
    # Reset all icons to default
    ModeUnlock.objects.all().update(icon='💰')

class Migration(migrations.Migration):
    dependencies = [
        ('main_app', '0004_auto_20250424_0218'),
    ]

    operations = [
        migrations.RunPython(update_mode_icons, reverse_mode_icons),
    ] 