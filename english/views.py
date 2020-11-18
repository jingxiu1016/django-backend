import datetime
import os
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework.views import APIView
from english.models import User, UserExtension, DailyLog, Word, Translation
from english.serializer import UserSerializer, UserExtensionSerializer, WordSerializer, TranslationSerializer
from english.utils.audio_synthetic import createWebSocket
from english.utils.jwt_auth import create_token
from english.extensions.auth import jwtQueryParamsBaseAuthentication

# Create your views here.
class UserRegisterApiView(APIView):
    '''用户注册视图'''

    authentication_classes = []

    def GetUsernameOf(self, username):
        if User.objects.filter(username=username):
            return True
        else:
            return False

    def get(self, request):
        '''用于测试是否已存在用户'''
        # 1 参数获取
        if not bool(request.query_params):
            return Response("这个get请求用于注册账号是验证数据库是否存在相同的用户名")
        else:
            username = request.query_params['username']
            # 2 数据校验
            data = {'status': 201}
            if self.GetUsernameOf(username=username):
                data['status'] = 204
                data['err_msg'] = '已存在用户'
            else:
                data['msg'] = '可创建用户'
            return Response(data=data)

    def post(self, request):
        # 1 获取数据
        username = request.data['username']
        password = request.data['password']
        nickname = request.data['nickname']
        email = request.data['email']
        avatar = request.FILES['avatar']
        get_user_data = {
            'username': username,
            'password': password,
            'nickname': nickname,
            'email': email,
            'avatar': avatar
        }
        # 2 数据校验
        ret_data = {}
        if self.GetUsernameOf(username=username):
            ret_data['status'] = 204
            ret_data['err_msg'] = '创建失败!已存在用户!'
            return Response(data=ret_data)
        serializer = UserSerializer(data=get_user_data)
        if serializer.is_valid():
            # 3 数据入库
            user = serializer.save()
            # 关联一个空的用户扩展信息
            user_extension = UserExtension.objects.create(user=user)
            extension_serializer = UserExtensionSerializer(instance=user_extension)
            ret_data['status'] = 201
            ret_data['msg'] = '创建成功!'
            ret_data['token'] = create_token({'id': user.id, 'name': user.username}, timeout=120)
            ret_data['userInfo'] = serializer.data
            ret_data['userExtension'] = extension_serializer.data
        # 4 返回信息
        return Response(data=ret_data)


class UserLoginApiView(APIView):
    '''用户登录视图'''

    authentication_classes = []

    def get(self, request):
        user = User.objects.get(id=1)
        user_extension = UserExtension.objects.get(user_id=user.id)
        user_serializer = UserSerializer(instance=user)
        extension_serializer = UserExtensionSerializer(instance=user_extension)
        data = user_serializer.data
        data['extension'] = extension_serializer.data
        return Response(data)

    def post(self, request):
        data = {}
        # 1 获取数据
        username = request.data['username']
        password = request.data['password']
        # 2 数据校验
        user = User.objects.get(username=username)
        if user.password != password:
            data['status'] = 204
            data['err_msg'] = '登录失败!密码错误!'
        else:
            extension = UserExtension.objects.get(user_id=user.id)
            extension_serializer = UserExtensionSerializer(instance=extension)
            user_serializer = UserSerializer(instance=user)
            data['status'] = 201
            data['msg'] = '登录成功!欢迎进入'
            data['token'] = create_token({'id': user.id, 'name': user.username}, timeout=120)
            data['userInfo'] = user_serializer.data
            data['userExtension'] = extension_serializer.data
        # 3 返回数据
        return Response(data=data)


class WordApiView(APIView):

    authentication_classes = [jwtQueryParamsBaseAuthentication]

    def getWordOf(self, word):
        if Word.objects.filter(word=word):
            return True
        else:
            return False

    def get(self, request):
        if not bool(request.query_params):
            return Response("这个get请求用于注册账号是验证数据库是否存在相同的用户名")
        else:
            word = request.query_params['word']
            # 2 数据校验
            data = {'status': 201}
            if self.getWordOf(word=word):
                data['status'] = 204
                data['err_msg'] = '云端已存在单词'
            else:
                data['msg'] = '可录入单词'
            return Response(data=data)

    def post(self, request):
        '''用于增加单词
        json格式,,words 保存所有记录的单词,是个数组
        translation 保存单词的不同词性的释义,是个数组,每个元素是一个对象,这个对象包含单词的词性和相对是释义
        mean 保存单词相对词性的释义,是个键值
        {
            "user_id":1,
            "words":[
                {
                    "word":"test",
                    "translation":[
                        {
                            "part_speech":"n",
                            "mean":"测试"
                        }
                    ]
                }
            ]
        }
        '''
        ret_data = {}
        get_data = request.data
        word_total = 0      # 统计上传了多少了单词
        # 1 根据userid 确定是哪位用户打卡单词,获取user对象
        user = User.objects.get(id=get_data['user_id'])
        for word_for in get_data['words']:
            # 确定单词位置
            # 2 反序列化WordSerializer
            word_data = {
                'user': user.id,
                'word': word_for['word']
            }
            word_serializer = WordSerializer(data=word_data)
            # 3 数据校验
            result = word_serializer.is_valid()
            if result:
                # 4 入库
                word = word_serializer.save()
                for trans in word_for['translation']:
                    # 根据单词对象,关联创建释义对象
                    # 1 反序列化TranslationSerializer
                    trans_data = {
                        'word': word.id,
                        'the_part_of_speech': trans['part_speech'],
                        'translation': trans['mean']
                    }
                    trans_serializer = TranslationSerializer(data=trans_data)
                    # 2 数据校验
                    if trans_serializer.is_valid():
                        trans_serializer.save()
            else:
                ret_data['status'] = 204
                ret_data['err_msg'] = '上传错误'
                return Response(data=ret_data)
            # 循环统计单词量
            word_total += 1
        # 需要本次上传了多少个单词并提交到DailyLog中
        today = datetime.datetime.now().date()
        if(DailyLog.objects.filter(date=today)):
            '''如果今日已经打过卡了,那么需要在原有的基础上,log中的total需要增加单词量
                extension中的总单词量,单日最高需要更新
            '''
            log = DailyLog.objects.get(date=today)
            log.total += word_total
            log.save()
            # 可返回用户总记单词量,然后赋值给vuex中的userextension中
            extension = UserExtension.objects.get(id=user.id)
            extension.the_total += word_total   # 计算总数据
            # 判断单日最高记词
            if extension.singer_total <= log.total:
                extension.singer_total = log.total
            extension.save()
        else:
            '''如果今日未打卡,则新增log记录,extension的总量,单日最高需要更新,持续打卡天数增加1'''
            log = DailyLog.objects.create(user_id=user.id,total=word_total)
            log.save()
            extension = UserExtension.objects.get(id=user.id)
            extension.the_total += word_total  # 计算总数据
            if extension.singer_total <= log.total:
                extension.singer_total = log.total
            # 更新持续打卡天数
            extension.continuous_days += 1
            extension.save()
        ret_data['status'] = 201
        ret_data['msg'] = "上传成功!本次打卡{}个单词".format(word_total)
        return Response(data=ret_data)


class UserInfoApiView(APIView):
    '''用于前端页面刷新时,重新获取用户的数据'''
    authentication_classes = [jwtQueryParamsBaseAuthentication]
    def get(self,request):
        data = {}
        if not request.query_params['user_id']:
            data['stauts'] = 204
            data['err_msg'] = '获取失败!'
            return Response(data=data)
        else:
            id = request.query_params['user_id']
            user = User.objects.get(id=id)
            extension = UserExtension.objects.get(user_id=user.id)
            extension_serializer = UserExtensionSerializer(instance=extension)
            user_serializer = UserSerializer(instance=user)
            data['status'] = 201
            data['msg'] = '获取成功'
            data['userInfo'] = user_serializer.data
            data['userExtension'] = extension_serializer.data
            # 需要给userExtension新增一个七天记词量和昨日记词数量
            data['userExtension']['yesterday_total'] = self.getDaysTotal()
            today = datetime.datetime.now().date()
            if DailyLog.objects.filter(date=today):
                daily_log = DailyLog.objects.get(date=today)
                today_num = daily_log.total
            else:
                today_num = 0
            data['userExtension']['sevenDay_total'] = self.getDaysTotal(days=7) + today_num
        return  Response(data=data)

    def getDaysTotal(self,days=1):
        today = datetime.datetime.now().date()
        oneday = datetime.timedelta(days=1)
        # 计算这些天数的总量
        days_total = 0
        for d in range(days):
            if days == 1:
                yesterday = today - oneday
                if DailyLog.objects.filter(date=yesterday):
                    daily_log = DailyLog.objects.get(date=yesterday)
                    today = yesterday
                else:
                    break
                days_total = daily_log.total
            else:
                yesterday = today - oneday
                if DailyLog.objects.filter(date=yesterday):
                    daily_log = DailyLog.objects.get(date=yesterday)
                else:
                    break
                days_total += daily_log.total
                today = yesterday
                if d == 6:
                    break
        return days_total


class UserCheckApiView(APIView):
    '''用于请求判断用户是否打卡'''
    authentication_classes = [jwtQueryParamsBaseAuthentication]
    def get(self,request):
        data = {
            'status':201
        }
        today = datetime.datetime.now().date()
        if DailyLog.objects.filter(date=today):
            daily_log = DailyLog.objects.get(date=today)
            data['msg'] = '今日已打卡'
            data['today_total'] = daily_log.total
        else:
            data['status'] = 203
            data['msg'] = '今日未打卡'

        return Response(data=data)


class UserUpdateInfoApiView(APIView):

    authentication_classes = [jwtQueryParamsBaseAuthentication]
    def put(self,request):
        if request.data['modiUserInfo']:
            user_info = request.data['modiUserInfo']
        else:
            return Response({'status':204,'err_msg':'修改失败'})
        extension_info = user_info['extension']
        del user_info['extension']
        id = request.user['id']
        user = User.objects.get(id=id)
        user.nickname = user_info['nickname']
        user.email = user_info['email']
        extension = UserExtension.objects.get(user=user)
        extension.constellation = extension_info['constellation']
        extension.declaration = extension_info['declaration']
        user.save()
        extension.save()
        data ={
            'status':201,
            'msg':'信息修改成功'
        }
        return Response(data=data)


class sevenBarEchartsApiView(APIView):
    authentication_classes = [jwtQueryParamsBaseAuthentication]
    '''提供七天的数据给前台的bar视图'''
    def get(self,request):
        data = {
            'status': 201,
            'option': {
                'title': {'text': '七天打卡量'},
                'tooltip': {},
                'xAxis': {
                    'data': []
                },
                'yAxis': {},
                'series': [{
                    'name': '数量',
                    'type': 'bar',
                    'data': []
                }]
            },
            'msg': 'ok'
        }
        if not request.query_params['user_id']:
            data['stauts'] = 204
            data['msg'] = '获取失败!'
            return Response(data=data)
        else:
            user_id = request.query_params['user_id']
        get_seven_data = self.getDaysTotal(user_id=user_id)
        if(get_seven_data == None):
            data['stauts'] = 204
            data['err_msg'] = '获取失败!'
            return Response(data=data)
        else:
            data['option']['xAxis']['data'] = get_seven_data['date']
            data['option']['series'][0]['data'] = get_seven_data['day_num']
        return Response(data=data)

    def getDaysTotal(self, days=7,user_id=-1):
        if(user_id == -1):
            return None

        today = datetime.datetime.now().date()
        oneday = datetime.timedelta(days=1)
        data = {
            'date':[],
            'day_num':[]
        }
        for d in range(days):
            if DailyLog.objects.filter(date=today,user_id=user_id):
                daily_log = DailyLog.objects.get(date=today,user_id=user_id)
                data['date'].append(today.day)
                data['day_num'].append(daily_log.total)
            else:
                data['date'].append(today.day)
                data['day_num'].append(0)
            yesterday = today-oneday
            today = yesterday
        data['date'].reverse()
        data['day_num'].reverse()
        return data


class ThirtyLineEchartsApiView(APIView):
    '''提供三十天的数据给前台的line视图'''

    authentication_classes = [jwtQueryParamsBaseAuthentication]
    def get(self,request):
        data = {
            'status': 201,
            'option': {
                'title': {'text': '三十天打卡量'},
                'tooltip': {},
                'xAxis': {
                    'data':[]                     #get_thirty_data['date']
                },
                'yAxis': {},
                'series': [{
                    'name': '数量',
                    'type': 'line',
                    'data':[]                     #get_thirty_data['day_num']
                }]
            },
            'msg': 'ok',
            'thirtyDaysCheckPos':[]               #get_thirty_data['thirtyDaysCheckPos']
        }
        user_id = request.user['id']
        get_thirty_data = self.getDaysTotal(user_id=user_id)
        if get_thirty_data == None:
            data['status'] == 204
            data['msg'] == '获取失败'
        else:
            data['option']['xAxis']['data'] =  get_thirty_data['date']
            data['option']['series'][0]['data'] = get_thirty_data['day_num']
            data['thirtyDaysCheckPos'] = get_thirty_data['thirtyDaysCheckPos']
        return Response(data=data)

    def getDaysTotal(self, days=30,user_id = -1):
        if(user_id == -1):
            return None

        today = datetime.datetime.now().date()
        oneday = datetime.timedelta(days=1)
        data = {
            'date': [],
            'day_num': [],
            'thirtyDaysCheckPos':[]
        }
        # 通过user_id从日志表获取用户日志总数
        user_log_counter = DailyLog.objects.all().filter(user_id=user_id).count()
        for d in range(days):
            # if d > user_log_counter:
            #     break
            # 如果today在日志中存在,则获取到数据,添加标志1,否则0
            # 如果日志表中不足三十天,则返回用户以存在的天数
            if DailyLog.objects.filter(date=today,user_id=user_id):
                daily_log = DailyLog.objects.get(date=today,user_id=user_id)
                data['thirtyDaysCheckPos'].append({
                    'date': today.strftime('%Y-%m-%d'),
                    'pos':1
                })
                data['date'].append(today.day)
                data['day_num'].append(daily_log.total)
            else:
                data['thirtyDaysCheckPos'].append({
                    'date': today.strftime('%Y-%m-%d'),
                    'pos': 0
                })
                data['date'].append(today.day)
                data['day_num'].append(0)
            yesterday = today - oneday
            today = yesterday
        data['date'].reverse()
        data['day_num'].reverse()
        return data

class WordListApiView(APIView):

    authentication_classes = [jwtQueryParamsBaseAuthentication]

    def get(self,request):
        # 获取用户id
        user_id = request.user['id']
        # 获取用户的所有单词
        words = Word.objects.all().filter(user_id=user_id)
        wordCounter = words.count()
        # 序列化数据
        words_data = WordSerializer(instance=words,many=True).data
        # 循环遍历所获得的用户上传的单词序列,并获取对应单词的释义
        for word in words_data:
            if Translation.objects.filter(word_id=word['id']):
                trans = Translation.objects.all().filter(word_id=word['id'])
                trans_data = TranslationSerializer(instance=trans,many=True).data
            word.update({"translation":trans_data})
        # 生成paginator对象,定义每页显示10条记录
        paginator = Paginator(words_data,10)
        # 从前端获取到当前的页码数,默认为1
        if 'page' in request.query_params:
            page = request.query_params['page']
        else:
            return Response({'status':204,'err_msg':'获取失败,参数错误'})
        currentPage = int(page)
        ret_data = {
            'wordCounter':wordCounter
        }
        try:
            ret_data['word_list'] = list(paginator.page(currentPage))
            ret_data['status'] = 201
            ret_data['msg'] = '获取成功'
        except PageNotAnInteger:
            # 如果不是正确的整形页码,返回第一页的数据
            ret_data['word_list'] = list(paginator.page(1))
            ret_data['status'] = 204
            ret_data['err_msg'] = '不是正确的页码'
        except EmptyPage:
            # 如果用户获取的页码不再系统的页码列表中,显示最后的一页
            ret_data['word_list'] = list(paginator.page(paginator.num_pages))
            ret_data['status'] = 204
            ret_data['err_msg'] = '已到达最后一页'
        return Response(data=ret_data)


class WorldDateListApiView(APIView):
    '''用户用户前端点击日历获取到每日的所打卡单词'''
    authentication_classes = [jwtQueryParamsBaseAuthentication]

    def get(self,request):
        ret_data = {}
        # 获取用户id
        user_id = request.user['id']
        # 获取date
        if 'date' in request.query_params:
            get_date = request.query_params['date']
        else:
            ret_data['status'] = 204
            ret_data['err_msg'] = '未获得日期'
            return Response(data=ret_data)
        # 如果日志记录中能够获得到该用户当天的记录,则可返回,否则可确定当天未打卡
        if DailyLog.objects.filter(user_id=user_id,date=get_date):
            word_list = Word.objects.all().filter(date=get_date)
            word_list = WordSerializer(instance=word_list,many=True).data
            # 循环遍历所获得的用户上传的单词序列,并获取对应单词的释义
            for word in word_list:
                if Translation.objects.filter(word_id=word['id']):
                    trans = Translation.objects.all().filter(word_id=word['id'])
                    trans_data = TranslationSerializer(instance=trans, many=True).data
                word.update({"translation": trans_data})
            ret_data['status'] = 201
            ret_data['msg'] = '获取成功'
            ret_data['word_list'] = word_list
        else:
            ret_data['status'] = 204
            ret_data['err_msg'] = '当天未打卡'
        return Response(data=ret_data)


class AudioApiView(APIView):
    authentication_classes = [jwtQueryParamsBaseAuthentication]

    def get(self,request):
        if 'word' in request.query_params:
            word = request.query_params['word']
        else:
            return Response({
                'status':204,
                'err_msg':'获取失败!'
            })
        createWebSocket(word).start()
        # 成功获取到单词转语音,之后需要和前台进行交互

        ret_data = {
            'status':201,
            'msg':'获取成功',
        }
        if os.path.exists(str(settings.BASE_DIR)+'\\'+'media/audio/word.mp3'):
            ret_data['audioURL'] = 'media/audio/word.mp3'
        return Response(data=ret_data)