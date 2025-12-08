
def user_authenticated(request):
    return {'user_authenticated': request.session.get('user_id') is not None}