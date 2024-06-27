from django.urls import path
from .views import home,handle_user_choice,handle_bot_style,createbot,chat_with_bot

urlpatterns = [

    path('v1/<int:botid>/home/', home, name='home'),
    path('v1/<int:botid>/handle_user_choice/', handle_user_choice, name='handle_user_choice'),
    path('v1/<int:botid>/botstyle/', handle_bot_style, name='handle_bot_style'),
    path('v1/<int:botid>/createbot/', createbot, name='createbot'),
    path('v1/<int:botid>/chat/', chat_with_bot, name='chat_with_bot'),

]
