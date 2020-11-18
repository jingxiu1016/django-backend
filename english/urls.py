"""******************************** 开始
    author:惊修
    time:$
   ******************************* 结束"""
from django.urls import path
from english.views import *
app_name = 'english'
urlpatterns = [
    path('register',UserRegisterApiView.as_view(),name='register'),
    path('login',UserLoginApiView.as_view(),name='login'),
    path('userinfo',UserInfoApiView.as_view(),name='userInfo'),
    path('word',WordApiView.as_view(),name='word'),
    path('check',UserCheckApiView.as_view(),name='check'),
    path('sevenBar',sevenBarEchartsApiView.as_view(),name='sevenBar'),
    path('thirtyLine',ThirtyLineEchartsApiView.as_view(),name='thirtyLine'),
    path('update',UserUpdateInfoApiView.as_view(),name='update'),
    path('list',WordListApiView.as_view(),name='list'),
    path('dateList',WorldDateListApiView.as_view(),name='dateList'),
    path('audio',AudioApiView.as_view(),name='audio')
]