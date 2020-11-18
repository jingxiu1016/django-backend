"""******************************** 开始
    author:惊修
    time:$
   ******************************* 结束"""
from rest_framework import serializers
from english.models import *


class UserExtensionSerializer(serializers.ModelSerializer):
    '''用户扩展信息序列化器'''
    class Meta:
        model = UserExtension
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    '''用户模型序列化器'''
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        exclude = ('last_login', 'first_name', 'last_name', 'is_staff', 'date_joined', 'created_time', 'groups',
                   'user_permissions')

    def create(self, validated_data):
        return User.objects.create(**validated_data)


class WordSerializer(serializers.ModelSerializer):
    '''单词模型序列化器'''

    class Meta:
        model = Word
        fields = '__all__'

    def create(self, validated_data):
        return Word.objects.create(**validated_data)


class TranslationSerializer(serializers.ModelSerializer):
    '''翻译序列化器'''
    class Meta:
        model = Translation
        fields = '__all__'

    def create(self, validated_data):
        return Translation.objects.create(**validated_data)


class DailyLogSerializer(serializers.ModelSerializer):
    model = DailyLog
    fields = '__all__'
