from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from django.utils.timezone import now

'''
    用户记录每天学习的单词,cle
    可以录入书本上学习的单词
    单词不限定个数,记录日期,
    保存单词的释义,
'''
class User(AbstractUser):
    '''自定义用户类'''
    avatar = models.ImageField(upload_to='media/user_avatar/%Y/%m/%d',blank=True,verbose_name='头像')
    nickname = models.CharField(max_length=20,blank=None,verbose_name='昵称')
    email = models.EmailField(blank=None,verbose_name='邮箱')
    created_time = models.DateTimeField(default=now,verbose_name='创建时间')

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ('-created_time',)

    def __str__(self):
        return self.username



class Word(models.Model):
    '''单词表'''
    user = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name='用户')
    word = models.CharField(max_length=30,verbose_name='单词')
    date = models.DateField(default=now, verbose_name='记录日期')

    class Meta:
        db_table = 'word'
        verbose_name = '单词'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.word


class Translation(models.Model):
    '''翻译'''
    choices = (
        ('1', 'n.'),
        ('2', 'c.'),
        ('3', 'u.'),
        ('4', 'v.'),
        ('5', 'vt.'),
        ('6', 'vi.'),
        ('7', 'adv.'),
        ('8', 'aux.v'),
        ('9', 'adj.'),
        ('10', 'art.'),
        ('11', 'int.'),
        ('12', 'o.'),
        ('13', 'oc.'),
        ('14', 's.'),
        ('15', 'sc.'),
        ('16', 'prep.'),
        ('17', 'pron')
    )
    word = models.ForeignKey(Word,on_delete=models.CASCADE,verbose_name='单词')
    the_part_of_speech = models.CharField(max_length=10,choices=choices,verbose_name='词性')
    translation = models.CharField(max_length=50,verbose_name='释义')

    class Meta:
        db_table = 'Translation'
        verbose_name = '翻译表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.translation


class UserExtension(models.Model):
    '''用户扩展信息'''
    choices=(
        ('Aries', 'Aries'),         #白羊
        ('Taurus', 'Taurus'),       #金牛
        ('Gemini', 'Gemini'),       #双子
        ('Cancer', 'Cancer'),       #巨蟹
        ('Leo', 'Leo'),             #狮子
        ('Virgo', 'Virgo'),         #处女
        ('Libra', 'Libra'),         #天秤
        ('Scorpio', 'Scorpio'),     #天蝎
        ('Sagittarius', 'Sagittarius'),#射手
        ('Capricorn', 'Capricorn'), #魔蝎
        ('Aquarius', 'Aquarius'),   #水瓶
        ('Pisces', 'Pisces'),       #双鱼
    )
    user = models.ForeignKey(User,models.CASCADE,verbose_name='用户')
    sex = models.CharField(max_length=10,verbose_name='性别',default='男')
    constellation = models.CharField(max_length=20,choices=choices,default=choices[0][0],verbose_name='星座',blank=True)
    declaration = models.CharField(max_length=200,blank=True,verbose_name='宣言',default='没有啥想说的')
    the_total = models.IntegerField(default=0,verbose_name='总记词数')
    singer_total = models.IntegerField(default=0,verbose_name='单日最高')
    yesterday_tag = models.BooleanField(default=False,verbose_name='昨日打卡标记')
    continuous_days = models.IntegerField(default=0, verbose_name='连续打卡天数')

    class Meta:
        db_table = 'UserExtension'
        verbose_name = '用户信息扩展表'
        verbose_name_plural = verbose_name

    def __int__(self):
        return self.user_id


class DailyLog(models.Model):
    '''记录每日打卡用户所记的单词量'''
    user = models.ForeignKey(User,models.CASCADE,verbose_name='用户')
    date = models.DateField(default=now,verbose_name='日期')
    total = models.IntegerField(default=0, verbose_name='数量')

    class Meta:
        db_table = 'DailyLog'
        verbose_name = '用户记录日志表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.date.strftime('%Y-%m-%d')

