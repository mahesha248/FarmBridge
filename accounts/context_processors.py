def tab_token(request):

    token = request.GET.get("tab_token")

    if not token:
        token = request.POST.get("tab_token")

    return {
        "tab_token": token
    }