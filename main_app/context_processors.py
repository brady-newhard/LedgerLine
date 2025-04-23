from .models import ModeUnlock

def user_modes(request):
    """
    Context processor that adds unlocked modes to all templates
    """
    if request.user.is_authenticated:
        unlocked_modes = ModeUnlock.objects.filter(user=request.user, is_unlocked=True)
        return {
            'unlocked_modes': unlocked_modes,
            'has_unlocked_modes': unlocked_modes.exists()
        }
    return {
        'unlocked_modes': None,
        'has_unlocked_modes': False
    } 