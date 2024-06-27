from django.urls import path
from .views import home,handle_user_choice,handle_bot_style,createbot,chat_with_bot

urlpatterns = [

    path('home/', home, name='home'),
    path('handle_user_choice/<int:uid>/<int:projectid>/<int:botid>/', handle_user_choice, name='handle_user_choice'),
    path('handle_user_choice/<int:uid>/<int:projectid>/<int:botid>/botstyle/', handle_bot_style, name='handle_bot_style'),
    path('handle_user_choice/<int:uid>/<int:projectid>/<int:botid>/createbot/', createbot, name='createbot'),
    path('chat/<uid>/<projectid>/<botid>/', chat_with_bot, name='chat_with_bot'),

]
