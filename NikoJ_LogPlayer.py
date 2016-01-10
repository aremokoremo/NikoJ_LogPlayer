# -*- coding: utf-8 -*-

""" NicoJ_LogPlayer

ニコニコ実況の過去ログを取得し、デジタルテロッパに転送します
"""
__author__ = 'aremokoremo'
__version__ = '1.0'

import sys
import time
from xml.etree.ElementTree import *
import urllib, urllib2
import httplib
import cookielib
import datetime
import re
import os
import codecs
import traceback
import getpass

#####################################################
# グローバル変数
#####################################################
# Trueにするとログが大量に出ます。通常はFalseで。
# 起動時に -dオプションを指定するとTrueに変わります
debug = False


#####################################################
# 共通関数
#####################################################
def wait(sec):
    """
    [Description]
        waitを入れる関数です
    
    [Arguments]
        sec : waitさせたい秒数
    """
    print str(sec) +  " sec wait"
    for i in range(sec+1):
        time.sleep(1)
        print " : "


def PrintFuncStart(funcname):
    """
    [Description]
        (Debug用) 関数開始を示すログを出します
    
    [Arguments]
        funcname : 関数名
    """
    if debug == True:
        print ""
        print "[DBG] VV-- " + funcname + " ----------------(start)--VV"


def PrintFuncEnd(funcname):
    """
    [Description]
        (Debug用) 関数終了を示すログを出します
    
    [Arguments]
        funcname : 関数名
    """
    if debug == True:
        print "[DBG] AA-- " + funcname + " ----------------(end)----AA"
        print ""

def PrintErrInfo(str):
    """
    [Description]
        (Debug用) エラーログを出します。
        ただし、debugフラグが有効なときのみ出力します
        あからさまにエラーが発生したときのログ出力用。
    
    [Arguments]
        str : ログ出力内容
    """
    print "[ERROR]  " + str


def PrintDbgInfo(str):
    """
    [Description]
        (Debug用) 一般情報ログを出します。
        ただし、debugフラグが有効なときのみ出力します
        エラーとは言えないけれど、とりあえず情報を出力したい場合用。
    
    [Arguments]
        str : ログ出力内容
    """
    if debug == True:
        print "[DBG][Info]   " + str

def PrintInput(str):
    """
    [Description]
        (Debug用) 関数のインプットをログ出力します。
        ただし、debugフラグが有効なときのみ出力します
    
    [Arguments]
        str : インプットの内容
    """
    if debug == True:
        print "[DBG][Input]  " + str

def PrintOutput(str):
    """
    [Description]
        (Debug用) 関数のアウトプットをログ出力します。
        ただし、debugフラグが有効なときのみ出力します
    
    [Arguments]
        str : アウトプットの内容
    """
    if debug == True:
        print "[DBG][Output] " + str



def convertYYYYMMDDHHMMSS_toPosixTime(yyyymmddhhmmss):
    """
    [Description]
        日時をYYYYMMDDHHMMSSのフォーマットから posix時間に変換します。
    
    [Arguments]
        yyyymmddhhmmss : 日時。YYYYMMDDHHMMSSのフォーマット（例:20140301143100）

    [Return value]
        posix時間 : 成功時 
        -1        : 指定されたYYYYMMDDHHMMSSの長さが短い 
        -2        : 存在しない日時が指定された
    """
    PrintFuncStart("convertYYYYMMDDHHMMSS_toPosixTime")
    PrintInput("yyyymmddhhmmss = %s" % yyyymmddhhmmss)

    ret = -1

    # おおまかなチェックrough check (length check)
    if len(yyyymmddhhmmss) != 14:
        PrintErrInfo("%s 不正な日時です。YYYYMMDDHHMMSS の形式で入力してください" % yyyymmddhhmmss) 
        PrintOutput("-1")
        PrintFuncEnd("convertYYYYMMDDHHMMSS_toPosixTime")
        return -1

    # posix時間に変換
    str_year    = yyyymmddhhmmss[0:4]
    str_month   = yyyymmddhhmmss[4:6]
    str_day     = yyyymmddhhmmss[6:8]
    str_hour    = yyyymmddhhmmss[8:10]
    str_minutes = yyyymmddhhmmss[10:12]
    str_seconds = yyyymmddhhmmss[12:14]

    year    = int(str_year)
    month   = int(str_month)
    day     = int(str_day)
    hour    = int(str_hour)
    minutes = int(str_minutes)
    seconds = int(str_seconds)

    try:
        posixtime = int(time.mktime(datetime.datetime(year,month,day,hour,minutes,seconds).timetuple()))
    except ValueError:
        PrintErrInfo("存在しない日時です")
        PrintOutput("%d " % -2) 
        PrintFuncEnd("convertYYYYMMDDHHMMSS_toPosixTime")
        return -2

    PrintOutput("%d " % posixtime) 
    PrintFuncEnd("convertYYYYMMDDHHMMSS_toPosixTime")
    return posixtime


def convertProhibitedXmlChar(input):
    """
    [Description]
        文字列中に含まれる "xmlで禁止されている文字" を
        xml内で使える形に変換します

        & --> &#38
        < --> &#60
        > --> &#62
        " --> &#34
        ' --> &#39
     
    [Arguments]
        input : 文字列

    [Return value]
        string : 変換後文字列
    """
    string = input

    if string != None:

        # & &#38;
        string = string.replace("&","&#38;")

        # < &#60;
        string = string.replace("<","&#60;")

        # > &#62;
        string = string.replace(">","&#62;")

        # " &#34;
        string = string.replace("\"","&#34;")

        # ' &#39;
        string = string.replace("'","&#39;")

    return string



#####################################################
# ニコニコ実況関連クラス
#####################################################
class NicoJk():
    """
    ニコニコ実況関連のクラスです。
    アカウント管理、ログイン、過去ログダウンロードをしたりします
    """
    configfileDir = "config"
    configfileName = "nico_account.txt"
    configfilePath = "%s/%s" % (configfileDir, configfileName)

    def __init__(self):
        """
        [Description]
            初期化関数
        """
        PrintFuncStart("__init__")
        self.account = {}

        PrintFuncEnd("__init__")

    def isConfigFileExisting(self):
        """
        [Description]
            設定ファイルの存在有無を確認します
     
        [Return value]
            True  : 存在する
            False : 存在しない
        """
        PrintFuncStart("isConfigFileExisting")

        ret = os.path.exists(NicoJk.configfilePath)

        PrintFuncEnd("isConfigFileExisting")
        return ret


    def getAccountInfo(self):
        """
        [Description]
             ニコニコ動画アカウントの情報(メアド、パスワード)を取得します
    
        [Return value]
            account : マップ型でアカウント情報が返ります。キーは、'mail', 'password' です
        """
        PrintFuncStart("getAccountInfo")

        ret = self.account
        
        PrintOutput("mail=%s, password=%s" % (self.account['mail'], self.account['password']))
        PrintFuncEnd("getAccountInfo")
        return ret


    def saveConfig(self, mail, password):
        """
        [Description]
             アカウント情報を設定ファイルに保存します。

        [Arguments]
            mail     : ニコニコ動画アカウントのメールアドレス
            password : ニコニコ動画アカウントのパスワード

        """
        PrintFuncStart("saveConfig")
        PrintInput("mail=%s, password=%s" % (mail, password))

        if os.path.exists(NicoJk.configfileDir) == False:
            os.mkdir(NicoJk.configfileDir)

        f = open(NicoJk.configfilePath, 'w')
        f.write("%s:%s" % (mail, password))
        f.close 

        PrintFuncEnd("saveConfig")


    def loadConfigFile(self):
        """
        [Description]
            ニコニコ動画アカウント設定ファイルを読み込みます
    
        [Return value]
            True  : 成功
            False : 失敗 
        """
        PrintFuncStart("loadConfigFile")

        f = None
        str = None

        # ファイルオープン
        f = open(NicoJk.configfilePath, 'r')
        if f == None:
            PrintErrInfo("設定ファイルが見つかりません。config/nico_account.txt を作成してください")
            PrintFuncEnd("loadConfigFile")
            return False

        # 読み込み
        str = f.read()
        f.close()

        # 空かどうかのチェック
        if str == None:
            PrintErrInfo("設定ファイルが空です。\"mailaddress:password\" のフォーマットで記載してください")
            PrintFuncEnd("loadConfigFile")
            return False 

        # mail:passwordのフォーマットになってるかチェック
        items = str.split(':')
        if len(items) != 2:
            PrintErrInfo("設定ファイルの内容が不完全です。\":\" がありません。\"mailaddress:password\" のフォーマットで記載してください")
            PrintFuncEnd("loadConfigFile")        
            return False

        # それぞれの長さが0でないかチェック
        mail = items[0]
        password = items[1]

        if len(mail) == 0 or len(password) == 0:
            PrintErrInfo("設定ファイルの内容が不完全です。メアドもしくはパスワードがありません。 \"mailaddress:password\" のフォーマットで記載してください")
            PrintFuncEnd("loadConfigFile")        
            return False


        # 保持
        self.account['mail'] = mail
        self.account['password'] = password

        PrintDbgInfo("読み込み完了。(mail, password) = (%s, %s)" % (self.account['mail'], re.sub("[a-zA-Z0-9_]", "*", self.account['password'])))    

        PrintFuncEnd("loadConfigFile")
        return True


    def isValidJkChannel(self, jkNum):
        """
        [Description]
            指定されたテレビ局のチャンネルか、有効なものかどうか、チェックします
     
        [Arguments]
            jkNum : チャンネル 

        [Return value]
            True  : 有効
            False : 不正
        """
        PrintFuncStart("isValidJkChannel")
        PrintInput( "jkNum = %s" % jkNum)

        jkNumList = ["jk1", "jk2", "jk3", "jk4", "jk5", "jk6", "jk7", "jk8", "jk9", "jk10", "jk11", "jk12", "jk103" ]
        ret = False

        for item in jkNumList:
            if jkNum == item:
                ret = True
                break

        if ret == False:
            PrintErrInfo("%s は不正なチャンネルです" % jkNum)
        else:
            PrintDbgInfo("%s 有効なチャンネルです" % jkNum)
            PrintOutput("True")

        PrintFuncEnd("isValidJkChannel")
        return ret    

    def isValidDurarion(self, posix_startTime, posix_endTime):
        """
        [Description]
            指定された "過去ログ開始時刻/終了時刻"が不正でないか、チェックします
         
        [Arguments]
            posix_startTime : 過去ログ開始日時 (posix時間)
            posix_endTime   : 過去ログ終了日時

        [Return value]
            True  : 正常
            False : 不正
        """
        PrintFuncStart("isValidDurarion")
        PrintInput("posix_startTime = %d, posix_endTime = %d" % (posix_startTime,  posix_endTime)) 
        ret = False

        # 負の数は問答無用でエラー
        if posix_startTime < 0 or posix_endTime < 0:
            PrintErrInfo("posix timeは正である必要があります") 
            PrintFuncEnd("isValidDurarion")
            return False        

        # 開始時刻と終了時刻の時系列チェック
        if posix_startTime > posix_endTime:
            PrintOutput("開始時刻は終了時刻よりも先である必要があります") 
            PrintFuncEnd("isValidDurarion")
            return False

        # 過去ログDLなので、未来の日時が設定されてはならない
        posix_currentTime = int(time.time())
        if posix_endTime > posix_currentTime:
            PrintErrInfo("終了時刻は、過去である必要があります") 
            PrintFuncEnd("isValidDurarion")
            return False

        PrintOutput("True")
        PrintFuncEnd("isValidDurarion")
        return True


    def downloadLog(self, jkNum, startTime, endTime):
        """
        [Description]
            過去ログをダウンロードします
         
        [Arguments]
            jkNum     : チャンネル
            startTime : 過去ログ開始日時 (YYYYMMDDSSHHMMSS)
            endTime   : 過去ログ終了日時 (YYYYMMDDSSHHMMSS)

        [Return value]
            xml : 過去ログ (xmlフォーマット)
        """
        PrintFuncStart("downloadLog")

        # チャンネルチェック
        ret = self.isValidJkChannel(jkNum)
        if ret != True:
            PrintErrInfo("at isValidJkChannel()")
            PrintFuncEnd("getNicoJkLog")
            return None

        # posix時間に変換
        posix_startTime = convertYYYYMMDDHHMMSS_toPosixTime(startTime)
        posix_endTime   = convertYYYYMMDDHHMMSS_toPosixTime(endTime)
        if posix_startTime == -1 or posix_endTime == -1:
            PrintErrInfo("at invalid posix time")
            PrintFuncEnd("getNicoJkLog")
            return None

        # 開始時刻／終了時刻の正当性チェック
        ret = self.isValidDurarion(posix_startTime, posix_endTime)
        if ret != True:
            PrintErrInfo("at isValidDurarion()")
            PrintFuncEnd("getNicoJkLog")
            return None

        # cookie利用の準備
        PrintDbgInfo("prepare to use cookie")
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        # login
        PrintDbgInfo("login")
        URL_NICO_LOGIN = "https://secure.nicovideo.jp/secure/login"
        r = opener.open(URL_NICO_LOGIN, "mail=%s&password=%s" % (self.account['mail'], self.account['password']))

        # flv infoの取得
        PrintDbgInfo("get flv info")
        flvinfo = {}
        API_GETFLV = "http://jk.nicovideo.jp/api/v2/getflv"
        r = opener.open(API_GETFLV + "?v=%s&start_time=%d&end_time=%d" % (jkNum, posix_startTime, posix_endTime))
        flvinfo_str =  r.read()        
        flvinfo_tmp = flvinfo_str.split('&')
        for info in flvinfo_tmp:
            item = info.split('=')
            flvinfo[item[0]] = item[1] 

        PrintDbgInfo("ms=%s, http_port=%s, thread_id=%s" % (flvinfo['ms'], flvinfo['http_port'], flvinfo['thread_id']))


        # wayback keyの取得 (過去ログ取得の際に必要なキー)
        PrintDbgInfo("get wayback key")
        r = opener.open("http://jk.nicovideo.jp/api/v2/getwaybackkey?thread=%s" % flvinfo['thread_id'])
        waybackkey = r.read()
        PrintDbgInfo(waybackkey)

        # xml形式のログを取得
        PrintDbgInfo("get log xml")
        serverURL = "http://%s:%s/api/thread" % ( flvinfo['ms'], flvinfo['http_port'])
        posix_waybackStart = posix_endTime

        # 指定時刻から遡って○○件取得できる。一度に取得できる最大件数は1000件。
        # なので、まずは指定時刻として終了時刻を指定し、遡って1000件の取得を試みる。
        # 取得できたコメントの件数が1000件以上あるようなら、指定時刻を前にずらして、再度1000件の取得を試みる。
        commentsLists = []
        print "1000件分をダウンロード中"  
        while 1:
            # URL生成
            params = "?thread=%s&res_from=%s&version=%s&when=%d&user_id=%s&%s" % ( flvinfo['thread_id'], 
                                                                                    "-1000",
                                                                                    "20061206",
                                                                                    posix_waybackStart, 
                                                                                    flvinfo['user_id'], 
                                                                                    waybackkey)
            url = serverURL + params 
            PrintDbgInfo("url=%s" % url)

            # xmlをダウンロード
            r = opener.open(url)
            tempxml = r.read()

            # コメント抽出
            try:
                tree = fromstring(tempxml)
#            except xml.etree.ElementTree.ParseError:
            # except ExpatData:
            #     PrintErrInfo("xml.etree.ElementTree.ParseError")
            except Exception as e:
                print '=== exception info  ==='
                print 'type:' + str(type(e))
                print 'args:' + str(e.args)
                print 'message:' + e.message
                print 'e itself:' + str(e)
            items = tree.findall('.//chat')
            numOfComments = len(items)
            PrintDbgInfo ("%d comments loaded" % numOfComments)
            print "1000件ダウンロードしました\n"

            # コメントをlistに加えて保存 
            commentsListsTemp = commentsLists
            commentsLists = items

            for comment in commentsListsTemp:
                commentsLists.append(comment)

            cnt = 0
            for comment in commentsLists:
                if (cnt % 500) == 0:
                    PrintDbgInfo("%s %s" % (comment.get("date"), comment.text))
                cnt += 1

            print "合計%d件のコメントをDL済み\n" % len(commentsLists)

            # いまDLしたコメントのコメント数をチェック
            if numOfComments == 1000:
                # 1000件ジャストなら、まだ残りがあるとみなす。
                # いまDL下コメントのうち、一番古いコメントの時刻を、次の指定時刻とする
                next_waybackStart = commentsLists[0].get("date")
                PrintDbgInfo("次の指定時刻は%s" % next_waybackStart)

                if int(next_waybackStart) > posix_startTime:
                    posix_waybackStart = int(next_waybackStart)
                else:
                    break

                # サーバ負荷軽減のために、スリープさせる
                wait(3)

                print "\n次の1000件をダウンロード中"

            else:
                break

        # ログ開始時刻よりも古いログがあったら捨てる
        outputCommentList = []
        for comment in commentsLists:
            commentDate = int(comment.get("date"))
            if commentDate >=  posix_startTime :
                outputCommentList.append(comment)

        print "\n有効コメント%d件" % len(outputCommentList)

        if debug == True:
            cnt = 0
            PrintDbgInfo("（参考）はじめの50コメント")
            for comment in outputCommentList:
                if cnt < 50:
                    PrintDbgInfo("%s %s" % (comment.get("date"), comment.text))
                cnt += 1

        # 全部のコメントを足したxmlファイルを作成する
        print "\nログをxmlファイルに保存中（多少時間かかるかも）"

        header_template = u"""<?xml version="1.0" encoding="UTF-8"?>
<packet>
<thread resultcode="" thread="%s" last_res="" ticket="" revision="1" server_time=""/>
<view_counter video="0"/>
"""

        item_template = u""" <chat user_id="%s" thread="%s" date="%s" vpos="%s" no="%s" premium="%s" anonymity="%s" mail="%s">%s</chat>
"""

        hooter_template = u"""</packet>
"""

        xml = header_template % flvinfo['thread_id']
        for item in outputCommentList:
            #xml禁止文字が読めてしまうので、変換する
            comment = convertProhibitedXmlChar(item.text)

            xml += (item_template % (item.get('user_id'), 
                                    item.get('thread'), 
                                    item.get('date'), 
                                    item.get('vpos'), 
                                    item.get('no'), 
                                    item.get('premium'), 
                                    item.get('anonymity'), 
                                    item.get('mail'), 
                                    comment ))

        xml +=  hooter_template

        #print xml

        PrintFuncEnd("downloadLog")
        return xml


    def getNicoJkLog(self, jkNum, startTime, endTime):
        """
        [Description]
            過去ログを取得します。実DLならDLします。DL済みならそれを使います。
         
        [Arguments]
            jkNum     : チャンネル
            startTime : 過去ログ開始日時 (YYYYMMDDSSHHMMSS)
            endTime   : 過去ログ終了日時 (YYYYMMDDSSHHMMSS)

        [Return value]
            filename  : 過去ログのファイル名
        """
        PrintFuncStart("getNicoJkLog")
        ret = None
        xml = None

        # 既にダウンロード済みだった場合は終了。
        filename = "xml/%s-%s-%s.xml" % (jkNum, startTime, endTime)
        ret = os.path.exists(filename)
        if ret == True:
            PrintDbgInfo("%s is already existing" % filename)
            print "ダウンロード済みです！"
            PrintFuncEnd("getNicoJkLog")
            return filename

        # 過去ログをダウンロード
        xml = self.downloadLog(jkNum, startTime, endTime)
        if xml == None:
            PrintErrInfo("DL 失敗した模様")
            PrintFuncEnd("getNicoJkLog")
            return None

        # 過去ログををxml fileにして保存
        if os.path.exists("xml") == False:
            os.mkdir("xml")

        f = codecs.open(filename,"w","utf-8")
        f.write(xml)
        f.close()    

        PrintOutput(filename)
        PrintFuncEnd("getNicoJkLog")
        return filename


#####################################################
# デジタルテロッパ関連クラス
#####################################################
class TeloppaComment():
    """
    デジタルテロッパ用のコメントクラスです。
    """
    def __init__(self, text, time):
        """
        [Description]
            初期化
         
        [Arguments]
            text:コメント文言
            time:コメント時間

        [Return value]
            None
        """        
        self.text = text
        self.time = time
 

class Teloppa():
    """
    デジタルテロッパ関連のクラスです。
    IP設定、コメント再生したりします
    """

    configfileDir = "config"
    ipconfigfileName = "teloppa_ip_config.txt"
    ipconfigfilePath = os.path.join(configfileDir, ipconfigfileName)

    def __init__(self):
        """
        [Description]
            初期化
         
        [Arguments]
            None

        [Return value]
            None
        """        
        PrintFuncStart("Teloppa.__init__")

        self.posix_teloppaStartTime = 0
        self.posix_xmlStartTime = 0

        self.teloppaIP = ""
        self.teloppaurl = ""
        self.color = "3"

        self.comments = [] #TeloppaCommentのリスト

        PrintFuncEnd("Teloppa.__init__")

    def isIpConfigFileExisting(self):
        """
        [Description]
            設定ファイルの存在有無を確認します
         
        [Arguments]
            None

        [Return value]
            True  : 存在する
            False : 存在しない
        """
        PrintFuncStart("isIpConfigFileExisting")

        ret = os.path.exists(Teloppa.ipconfigfilePath)

        PrintFuncEnd("isIpConfigFileExisting")
        return ret

    def getIpConfig(self):
        """
        [Description]
            設定値を取得します
         
        [Arguments]
            None

        [Return value]
            IPアドレス
        """
        PrintFuncStart("getConfig")
        print self.teloppaIP

        ret = self.teloppaIP

        PrintOutput(ret)
        PrintFuncEnd("getConfig")
        return ret

    def saveIpConfig(self, ip):
        """
        [Description]
            設定値をファイルに保存します
         
        [Arguments]
            None

        [Return value]
            None
        """
        PrintFuncStart("saveIpConfig")
        PrintInput("ip address=%s" % (ip))

        if os.path.exists(Teloppa.configfileDir) == False:
            os.mkdir(Teloppa.configfileDir)

        f = open(Teloppa.ipconfigfilePath, 'w')
        f.write("%s" % ip)
        f.close 

        PrintFuncEnd("saveIpConfig")

    def changeColor(self, color):
        """
        [Description]
            文字色を変更します
         
        [Arguments]
            color

        [Return value]
            None
        """
        PrintFuncStart("changeColor")
        PrintInput("color=%s" % (color))

        self.color = color

        PrintFuncEnd("changeColor")


    def loadIpConfig(self):
        """
        [Description]
            設定ファイルを読み込みます
         
        [Arguments]
            None

        [Return value]
            True  : 成功
            False : 失敗
        """
        PrintFuncStart("loadIpConfig")
        ret = False

        f = None
        str = None

        #ファイルオープン
        f = open(Teloppa.ipconfigfilePath, 'r')
        if f == None:
            PrintErrInfo("設定ファイルがありません。config/teloppa_config.txt を作成してください")
            PrintFuncEnd("loadIpConfig")
            return False

        # 読み込み
        str = f.read()
        f.close()

        # 簡易チェックその１（中身があるかどうか）
        if str == None:
            PrintErrInfo("設定ファイルが空です。デジタルテロッパのIPアドレスを記載してください。例）192.168.11.2 ")
            PrintFuncEnd("loadIpConfig")
            return False 

        # 簡易チェックその２ (xxx.xxx.xxx.xxx　のフォーマットになってるかどうか)
        items = str.split('.')
        if len(items) != 4:
            print len(items)
            PrintErrInfo("設定ファイルの中身が、IPアドレスではありません。例）192.168.11.2 のように記載してください")
            PrintFuncEnd("loadIpConfig")        
            return False

        # 雑だけどチェック完了、、
        self.teloppaIP = str
        self.teloppaurl = "http://%s" % str
        PrintDbgInfo("ロード完了。テロッパURL=%s" % self.teloppaurl)

        PrintFuncEnd("loadIpConfig")
        return True


    def set_log(self, xmlfile, startTime):
        """
        [Description]
            過去ログのファイルをteloppaクラスに入力します。
         
        [Arguments]
            xmlfile   : コメントxmlファイルのファイルパス
            startTime : 過去ログ開始日時 (YYYYMMDDSSHHMMSS)

        [Return value]
            None
        """        
        PrintFuncStart("initialize")
        PrintInput("xmlfile=%s, startTime=%s"% (xmlfile, startTime))


        # # #read xml
        # tree = parse(xmlfile)
        # self.comments = tree.findall('.//chat')
        # PrintDbgInfo("%d 件のコメントがロードされました。" % len(self.comments))

        # #read xml
        tree = parse(xmlfile)
        temp_comments = tree.findall('.//chat')
        temp_comments.append(None)


        #１秒間にコメントが4件以上ある場合は文字列連結して4件にまとめる。（１秒に５件のリクエストがあるとけっこう止まるので）
        #１秒間にコメントが２０件以上あった場合は２０件目以降は捨てる。つまり、maxで 1秒間で "5コメントまとめたもの" x ４
        cnt = 0
        comment = temp_comments[cnt]
        prev_comment_time = 0
        sum_comments = ["","","",""]
        sum_comments_num = 0 # max 24
        sum_comments_index = 0

        while comment != None:
            posix_commentTime = int(comment.attrib['date'])

            if(posix_commentTime == prev_comment_time):# 一個前のコメントの時間と比較、おなじだったらまとめる
                if sum_comments_num <= 24:
                    if sum_comments_num >= 4:
                        sum_comments[sum_comments_index] += u"　"
                    sum_comments[sum_comments_index] += comment.text
                    sum_comments_index += 1
                    if sum_comments_index == 4:
                        sum_comments_index = 0
                sum_comments_num += 1

            else :
                #たまってるバッファを正式コメント配列にadd
                for var in range(0, 4):
                    if sum_comments[var] == "":
                        break
                    else:
                        self.comments.append(TeloppaComment(sum_comments[var], posix_commentTime))

                #prev_comment_timeを更新
                prev_comment_time = posix_commentTime

                #バッファクリアして、一番はじめの要素にコメント入れる
                sum_comments = ["","","",""]
                sum_comments[0] = comment.text
                sum_comments_num = 1
                sum_comments_index = 1

            cnt += 1    
            comment = temp_comments[cnt]


        self.comments.append(None)

        PrintDbgInfo("%d 件のコメントがロードされました。" % len(temp_comments))

        # for time management
        self.posix_xmlStartTime = convertYYYYMMDDHHMMSS_toPosixTime(startTime)

        PrintFuncEnd("initialize")



    def start(self):
        """
        [Description]
            コメント再生開始
        
        [Arguments]
            None
        
        [Return value]
            None
        """
        PrintFuncStart("start")
        cnt = 0
        comment = self.comments[cnt]

        teloppa_resp_time_s = 0
        teloppa_resp_time_e = 0

        # for time management
        self.posix_teloppaStartTime = time.time()

        while comment != None:
            posix_currentTime = time.time()
            posix_commentTime = int(comment.time)

            comment_delay = (posix_currentTime - self.posix_teloppaStartTime) - (posix_commentTime - self.posix_xmlStartTime)
            
            if comment_delay <= -0.2:#コメントの時間が未来だったら、Waitする
                idle_sleep_duration = (comment_delay) * (-1) - 0.02 
#                print "%f, %f" % (-comment_delay, idle_sleep_duration)
                time.sleep(idle_sleep_duration)
            elif comment_delay >= 0 and comment_delay <= 3:#再生
                localtime = time.localtime(posix_commentTime)

#                print "comment_delay %f" % comment_delay

                str_localtime = "%d/%02d/%02d %02d:%02d:%02d" % (localtime.tm_year, 
                                                        localtime.tm_mon, 
                                                        localtime.tm_mday, 
                                                        localtime.tm_hour, 
                                                        localtime.tm_min, 
                                                        localtime.tm_sec)


                print str_localtime + " " + comment.text
                teloppa_resp_time_s = time.time()
                self.sendStringToTeloppa(comment.text)
                teloppa_resp_time_e = time.time()
                teloppa_resp_time = teloppa_resp_time_e - teloppa_resp_time_s

                # 0.08秒弱かかる模様　かつ、１秒間に５回以上のリクエストで0.8秒くらい待たされる模様
                if teloppa_resp_time > 0.09: 
                    print "[WARN] teloppa slow response:%f[sec]" % teloppa_resp_time

                cnt += 1    
                comment = self.comments[cnt]

            elif comment_delay > 3:#遅れがひどい場合は捨てる
                print "[ERROR] comment drop... " + comment.text
                cnt += 1    
                comment = self.comments[cnt]

        PrintFuncEnd("start")



    def sendStringToTeloppa(self, comment):
        """
        [Description]
            コメントを一件ずつデジタルテロッパに送信
         
        [Arguments]
            comment : コメント文字列

        [Return value]
            None
        """
        PrintFuncStart("sendStringToTeloppa")
        PrintInput(comment)      

        data = urllib2.quote(comment.encode("utf-8")) 
        url = self.teloppaurl + "/user.cgi?data=" + data + "&color=" + self.color + "&speed=10"

        try:
            urllib2.urlopen(url)
        except httplib.BadStatusLine:
            #PrintErrInfo("httplib.BadStatusLine")
            # こればっかり返ってくるけど何？
            # たまに、異常に返ってくるの遅いときあるけど何？

            # info = sys.exc_info()
            # print '  %s' % str( info[1] )

            dummy = 0

        PrintFuncEnd("sendStringToTeloppa")


#####################################################
# ユーザ対話関連クラス
#####################################################
class UI():
    """
    ユーザ対話関連のクラスです。
    IP設定、アカウント設定、チャンネル設定、ログのダウンロード、再生開始等
    """

    howToQuit = " 終了したい場合は q を入力してEnterを押してください"
    yyyymmddhhmmssExample = " 例）2014/01/02 19:30:00 の場合 -> 20140102193000"


    # initialize
    def __init__(self, nico, teloppa):
        self.nico = nico
        self.teloppa = teloppa


    # 間合い用
    def pause(self):
        print ""
        time.sleep(1.5)

    # スクリプトのタイトルを表示
    def showTitle(self):
        print "\n%s\n%s\n%s" % ("========================================",
                                "  ニコニコ実況 過去ログ取得スクリプト",
                                "========================================" )


    # ユーザ入力
    def showPrompt(self, title, body):
        self.showSeparator()
        
        if body == None:
            ret = raw_input("[%s]\n\n> " % title)
        else:
            ret = raw_input("[%s]\n\n%s\n\n> " % (title, body))

        return ret

    # ユーザ入力(password)
    def showPromptForPassword(self, title, body):
        self.showSeparator()
        
        if body == None:
            ret = getpass.getpass("[%s]\n\n> " % title)
        else:
            ret = getpass.getpass("[%s]\n\n%s\n\n> " % (title, body))

        return ret

    # ユーザ入力 シンプル板
    def showPromptSimple(self, title):
        return self.showPrompt(title, None)

    # セパレーターを表示
    def showSeparator(self):
        print "\n---------------------------------------"

    # 文字色をユーザ入力
    def changeColor(self):
        while 1:
            colorList = " 0 : 白\n 1 : 赤\n 2 : 緑\n 3 : 青"
            color = self.showPrompt("文字色を入力", 
                                 "数字を入力してENTERを押してください。\n\n%s\n\n%s" % (colorList, self.howToQuit))

            #チェック
            if color == "0" or color == "1" or color == "2" or color == "3":
                print "\n%s が選択されました。" % color
                self.pause()
                return color
            elif color == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "無効な入力です"
                self.pause()


    # チャンネルをユーザ入力
    def inputChannel(self):
        while 1:
            chList = " 1 : NHK\n 2 : Eテレ\n 4 : 日テレ\n 5 : テレ朝\n 6 : TBS\n 7 : テレ東\n 8 : フジ\n 9 : MX\n 11 : tvk\n 103 : BSプレミアム"
            ch = self.showPrompt("チャンネルを入力", 
                                 "数字を入力してENTERを押してください。\n\n%s\n\n%s" % (chList, self.howToQuit))

            #チェック
            if ch == "1" or ch == "2" or ch == "4" or ch == "5" or ch == "6" or ch == "7" or ch == "8" or ch == "9" or ch == "11" or ch == "103":
                print "\n%s チャンネルが選択されました。" % ch
                self.pause()
                jkNum = "jk%s" % ch
                return jkNum
            elif ch == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "無効な入力です"
                self.pause()

    # ログ開始日時／終了日時をユーザ入力
    def inputTime(self):
        posix_currentTime = time.time()

        while 1:
            startTime = self.showPrompt("番組開始の時刻を入力", 
                                        "日時をYYYYMMDDHHMMSS のフォーマットで入力して、Enterを押してください。\n%s\n\n%s" 
                                        % (self.yyyymmddhhmmssExample, self.howToQuit))

            if startTime == "q":
                print "終了します"
                self.pause()
                quit()

            posix_startTime = convertYYYYMMDDHHMMSS_toPosixTime(startTime)

            if posix_startTime == -1: 
                print "%s --- フォーマット違反です" % startTime
                self.pause()
            elif posix_startTime == -2:
                print "%s --- 存在しない日時です" % startTime
            else:
                if (posix_currentTime - posix_startTime) < 0:
                    print "%s --- 未来が設定されています。過去の日時を設定してください。" % startTime
                    self.pause()
                else:
                    print "\n 開始時刻 %s が設定されました" % startTime
                    self.pause()
                    break

        while 1:
            endTime = self.showPrompt("番組終了の時刻を入力", 
                                        "日時をYYYYMMDDHHMMSS のフォーマットで入力して、Enterを押してください。\n%s\n\n%s" 
                                        % (self.yyyymmddhhmmssExample, self.howToQuit))

            if endTime == "q":
                print "終了します"
                self.pause()
                quit()

            posix_endTime = convertYYYYMMDDHHMMSS_toPosixTime(endTime)

            if posix_endTime == -1: 
                print "%s --- フォーマット違反です" % endTime
                self.pause()
            elif posix_endTime == -2:
                print "%s --- 存在しない日時です" % endTime
            else:
                if (posix_currentTime - posix_endTime) < 0:
                    print "%s --- 未来が設定されています。過去の日時を設定してください。" % endTime
                    self.pause()
                elif (posix_endTime - posix_startTime) < 0:
                    print "%s --- 開始時刻 (%s) よりも過去の日時が設定されています。" % (endTime, startTime)
                    self.pause()
                elif (posix_endTime - posix_startTime) > 10800:
                    print " 開始日時:%s\n 終了日時:%s\n\n長過ぎます！ ３時間以内になるようにしてください！\n(サーバ負荷軽減のため)" % (startTime, endTime)
                    self.pause()                    
                else:
                    print "\n 終了時刻 %s が設定されました" % endTime
                    self.pause()
                    break

        output = [startTime, endTime]

        return output

    # ログ取得を開始してよいかどうか、ユーザに確認
    def confirmToStartGettingLog(self, jkNum, startTime, endTime):

        while 1:
            input = self.showPrompt("確認", "ログ取得を開始します。\n\n チャンネル:%s\n 開始日時:%s\n 終了日時:%s\n\n 開始する場合は y\n 終了する場合は q\n\nを入力してENTERを押してください" 
                              % (jkNum[2:], startTime, endTime))

            if input == "y":
                print "\n取得開始しました"
                self.pause()
                return
            elif input == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "不正な入力です。"   
                self.pause()

    # ダウンロードが完了した由をユーザに通知
    def notifyGettingLogCompleted(self, xmlfile):
        print "\nログ取得完了！！ (%s に保存されています)\n" % xmlfile
        self.pause()

        #音を鳴らしてみる
        sys.stdout.write('\a')
        sys.stdout.flush()
 
     # 再生が完了した由をユーザに通知
    def notifyPlaybackCompleted(self):
        print "\n再生完了！！\n"

        #音を鳴らしてみる
        sys.stdout.write('\a')
        sys.stdout.flush()

        self.pause()

    # デジタルテロッパのコメント再生を開始してよいか、ユーザに確認
    def confirmStartingTeloppa(self):

        while 1:
            input = self.showPrompt("デジタルテロッパのコメント再生", " 開始する場合は y\n 終了する場合は q\n\nを入力してENTERを押してください")

            if input == "y":
                self.pause()

                print "\n"

                # 再生開始まで、カウントダウン
                cnt = 5
                for i in range(cnt):
                    print "%d秒後に開始します！\n     :" % cnt
                    time.sleep(1)
                    cnt -= 1

                print "START!!"
                self.showSeparator()

                return
            elif input == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "不正な入力です。"    

    # ニコニコ動画のアカウントをセーブ
    def saveNicoAccount(self):
        mail = ""
        password = ""

        while 1:
            # メアド入力
            while 1:
                mail = self.showPrompt("ニコニコ動画アカウント設定（メールアドレス）", 
                                        "メールアドレスを入力して、ENTERを押してください")
                if len(mail) == 0:
                    print "何も入力されていません\n"
                    self.pause()
                else:
                    print "mail=%s\n" % mail
                    self.pause()
                    break

            # パスワード入力（***みたいに隠したいけど、まあいいか、、、）
            while 1:
                password = self.showPromptForPassword("ニコニコ動画アカウント設定（パスワード）", 
                                            "パスワードを入力して、ENTERを押してください")
                if len(password) == 0:
                    print "何も入力されていません\n"
                    self.pause()
                else:
                    print "password=%s\n" % re.sub("[a-zA-Z0-9_]", "*", password)
                    self.pause()
                    break

            # 確認画面
            while 1:
                accountinfo = "あなたのアカウント設定は\n mail=%s\n password=%s\nです。\n\n" % (mail, re.sub("[a-zA-Z0-9_]", "*", password))
                input = self.showPrompt("確認",
                                        "%s こちらでよろしければ y\n やり直すには n\n 終了するには q\n\nを入力して ENTERを押してください" % accountinfo)
        
                if input == "y":
                    nico = NicoJk()
                    nico.saveConfig(mail, password)

                    print "ニコニコ動画のアカウント設定を保存しました"

                    return
                elif input == "n":
                    print "やり直します"
                    self.pause()
                    break
                elif input == "q":
                    print "終了します"
                    self.pause()
                    quit()
                else:
                    print "不正な入力です。\n"
                    self.pause()

    # ニコニコ動画のアカウントをload
    def loadNicoAccount(self):
        while 1:
            # 設定ファイルが無ければ、ユーザ入力
            if self.nico.isConfigFileExisting() == False:
                print "\nニコニコ動画のアカウントが設定されていません！"
                self.pause()
                self.saveNicoAccount()

            # 設定ファイルロード
            ret = self.nico.loadConfigFile()

            # 読み込んだ設定ファイルに不備があれば、設定し直す
            if ret == False:
                print "\n設定ファイルが不正です！　設定し直してください！"
                self.pause()
                self.saveNicoAccount()
            else:
                print "ニコニコ動画 アカウント設定をロードしました"
                break

    # デジタルテロッパのIP設定をセーブ
    def saveTeloppaIpConfig(self):
        ipadress = ""

        while 1:
            while 1:
                ipadress = self.showPrompt("デジタルテロッパ設定（IPアドレス）", 
                                        "IPアドレスを入力して、ENTERを押してください\n\n 例）192.168.11.3")
                if len(ipadress) == 0:
                    print "何も入力されていません\n"
                    self.pause()
                else:
                    print "ipadress=%s\n" % ipadress
                    self.pause()
                    break

            # 確認画面
            while 1:
                teloppasetting = "デジタルテロッパ設定は\n ip address=%s\nです。\n\n" % ipadress
                input = self.showPrompt("確認",
                                        "%s こちらでよろしければ y\n やり直すには n\n 終了するには q\n\nを入力して ENTERを押してください" % teloppasetting)
        
                if input == "y":
                    self.teloppa.saveIpConfig(ipadress)

                    print "デジタルテロッパの設定を保存しました"

                    return
                elif input == "n":
                    print "やり直します"
                    self.pause()
                    break
                elif input == "q":
                    print "終了します"
                    self.pause()
                    quit()
                else:
                    print "不正な入力です。\n"
                    self.pause()


    # デジタルテロッパの設定をload
    def loadTeloppaConfig(self):
        while 1:
            # IP設定ファイルが無ければ、ユーザ入力
            if self.teloppa.isIpConfigFileExisting() == False:
                print "\nデジタルテロッパのIPアドレス設定されていません！"
                self.pause()
                self.saveTeloppaIpConfig()

            # IP設定ロード
            ret = self.teloppa.loadIpConfig()

            # 読み込んだIP設定に不備があれば、設定し直す
            if ret == False:
                print "\nIP設定ファイルが不正です！　設定し直してください！"
                self.pause()
                self.saveTeloppaIpConfig()
            else:
                print "デジタルテロッパ IPアドレス設定をロードしました"
                break

    # 設定確認
    def confirmSettings(self):
        nicoAccount = self.nico.getAccountInfo()

        teloppaIP = self.teloppa.getIpConfig()

        currentSettings = "ニコニコ動画アカウント\n mail = %s\n password = %s\n\nデジタルテロッパ IPアドレス\n IP = %s" % (nicoAccount['mail'], 
                                                                                                                re.sub("[a-zA-Z0-9_]", "*", nicoAccount['password']), 
                                                                                                                teloppaIP)

        while 1:
            input = self.showPrompt("設定確認", 
                                    "%s\n\n この設定でよい場合は y\n 修正する場合は m\n 終了するには q\n\nを入力して、ENTERを押してください" 
                                    % currentSettings)
            if input == "y":
                print "OK\n"
                self.pause()
                return True
            elif input == "m":
                print "設定を修正します\n"
                self.pause()
                return False
            elif input == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "不正な入力です。\n"
                self.pause


    # 設定を修正
    def modifySettings(self):
        while 1:
            which = self.showPrompt("設定変更", 
                                    " ニコニコ動画アカウント設定のみ変更する場合は 1\n デジタルテロッパ設定のみ変更する場合は 2\n 両方変更する場合は 3\n 終了する場合は q\n\nを入力し、ENTERを押してください")
            if which == "1":
                print "ニコニコ動画アカウント設定を変更します\n"
                self.pause()
                self.saveNicoAccount()
                break
            elif which == "2":
                print "デジタルテロッパ設定を変更します\n"
                self.pause()
                self.saveTeloppaConfig()
                break
            elif which == "3":
                print "ニコニコ動画アカウント設定、デジタルテロッパ設定を変更します\n"
                self.pause()
                self.saveNicoAccount()
                self.saveTeloppaConfig()
                break
            elif input == "q":
                print "終了します"
                self.pause()
                quit()
            else:
                print "不正な入力です。\n"
                self.pause





#####################################################
# main 関数
#####################################################
if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)
    
    #debugログ設定
    debug = False
    if (argc == 2):
        print argvs[1]
        if argvs[1] == "-d":
            debug = True

    while 1:

        # 準備
        nico = NicoJk()
        teloppa = Teloppa()
        ui = UI(nico, teloppa)

        # (CUI) タイトル表示
        ui.showTitle()

        # (CUI) 各種設定
        while 1:

            # (CUI) ニコニコ動画 アカウント情報をロード
            ui.loadNicoAccount()

            # (CUI) デジタルテロッパ アカウント情報をロード
            ui.loadTeloppaConfig()

            # (CUI) 設定確認 
            ret = ui.confirmSettings()
            if ret == True:
                break
            else:
                # (CUI) 設定やりなおし
                ui.modifySettings()

        # (CUI) 文字色変更
        color = ui.changeColor()
        teloppa.changeColor(color)

        # (CUI) チャンネル入力
        jkNum = ui.inputChannel()

        # (CUI) 時刻入力
        datelist = ui.inputTime()

        startTime = datelist[0]
        endTime   = datelist[1]

        # (CUI) 過去ログ取得するか確認
        ui.confirmToStartGettingLog(jkNum, startTime, endTime)

        # 過去ログ取得開始
        xmlfile = nico.getNicoJkLog(jkNum, startTime, endTime)
        if xmlfile == None: 
            PrintErrInfo("at getNicoJkLog()")
            print "終了します。"
            quit()

        # (CUI) ログ取得完了通知
        ui.notifyGettingLogCompleted(xmlfile)

        # テロッパに過去ログをInput
        print "ログ再生準備をしています"
        teloppa.set_log(xmlfile, startTime)        
        print "\n再生準備完了！"
        time.sleep(1.5)

        # (CUI) テロッパへのコメント転送開始するかどうか確認
        ui.confirmStartingTeloppa()

        # テロッパへのコメント転送開始
        teloppa.start()

        # (CUI) 生成完了を通知
        ui.notifyPlaybackCompleted()





