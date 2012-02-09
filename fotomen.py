import urllib2, BeautifulSoup, time, re, string, os, thread

global IMGCOUNTER 
global STARTTIME

def get_page(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', 'Google Bot')
    urllib2.socket.setdefaulttimeout(10)
    failure_time = 0
    while (failure_time < 3):
        try:
            return urllib2.urlopen(request).read()
            break
        except:
            failure_time += 1
    return False

def write_error(error_info):
    fp_error = open('error_list.txt','a+')
    fp_error.write("%s\n"%(error_info))
    fp_error.close()
    
def get_page_number(url):
    page_number = 0
    content = urllib2.urlopen(url)
    get_page_info(url,content.read())
    soup = BeautifulSoup.BeautifulSoup(content)
    s1 = soup.find('div',{"class" : "subpage"})
    re_text = '<span>(\d{1,2})<\/span>'
    test_string = '<div class="subpage"><span id="pager-before">文章分页»</span> <span>1</span> <a href="http://fotomen.cn/2012/01/jing-dian/2/"><span>2</span></a> <a href="http://fotomen.cn/2012/01/jing-dian/3/"><span>3</span></a> </div>'
    result = re.findall(re_text, "%s"%(s1))
    if result == []:
        page_number = 1
    else:
        page_number = string.atoi(result[-1])
    return page_number

def get_page_info(url,content):
    re_title = '<title>(.*?)</title>'
    re_tags = 'rel="tag">(.*?)</a>'
    tags = re.findall(re_tags, content)
    title = re.findall(re_title, content)
    fp = open("page_info.txt","w+")
    fp.write("%s||%s||" % (url,title[0]))
    for tag in tags:
        fp.write("%s||" % (tag))
    fp.write("\n")
    fp.close()

def get_page_list():
    url = "http://fotomen.cn/category/appreciation/"
    content = get_page(url)
    re_max_page = 'http://fotomen.cn/category/appreciation/page/(.*?)/'
    arr = re.findall(re_max_page, content)
    max_page_number = arr[len(arr)-1]
    max_page_number = string.atoi(max_page_number)
    latest = ""
    if(os.path.exists('page_list.txt')):
        fp = open("page_list.txt",'r')
        latest = fp.readline();
        fp.close()
        latest = latest.split('|')[2][:-1]
        
    
    for page_number in range(1,max_page_number + 1):
        target = "%spage/%d" % (url,page_number)
        content = get_page(target)
        re_page = 'class="readmore" href="(.*?)"'
        arr = re.findall(re_page, content)
        fp = open("page_list_new.txt",'a+')
        for page in arr:
            if (page == latest):
                print "done\n%s" % (page )
                fp.close()
                exit(0)
            print "find page %s"%(page)
            fp.write("%s|%s|%s\n"%(time.ctime(),target,page))
        fp.close()
        

def load_page_list_file():
    page_list_arr = []
    fp = open('page_list.txt','r')
    lines = fp.readlines()
    for line in lines:
        page_list_arr.append(line.split('|')[2][:-1]);
    return page_list_arr

def save_img(url,name,lock):
    year = url.split('/')[3]
    month = url.split('/')[4]
    filename = url.split('/')[5]
    dir_name = "%s/%s/%s" % (year,month,name)
    fp = open("%s/%s" % (dir_name, filename),'wb')
    content = get_page(url)
    if(content == False):
        write_error("%s|%s\n"%(name,url))
    else:
        fp.write(content)
    fp.close()
    print "done_img |%s|%s|%s"%(url,name,time.ctime())
    lock[0] += 1
    
def download_img(url,page_number):
    global IMGCOUNTER
    global STARTTIME
    thread_number = 10
    for i in range(1,page_number+1):
        page_url = "%s%d" % (url,i)
        content = get_page(page_url)
        if(content == False):
            
            return False
        year = url.split('/')[3]
        month = url.split('/')[4]
        name = url.split('/')[5]
        dir_name = "%s/%s/%s" % (year,month,name)
        if (os.path.exists(dir_name) == False):
            os.makedirs(dir_name)
        re_text = 'href="(http://image.fotomen.cn/' + year + '/' + month +'/(.*?).jpg)"'
        arr = re.findall(re_text, content)
        if (len(arr) == 0):
            if (os.path.exists("error_pages") == False):
                os.makedirs("error_pages")
            error_fp = open("error_pages/%d_%d_%s_%d.html" % (year,month,name,i),'w')
            error_fp.write(content)
            error_fp.close()
            continue
        lock = [thread_number]
        for img in arr:
                while(1):
                    time.sleep(0.1)
                    if(lock[0] > 0):
                        lock[0] -= 1
                        thread.start_new_thread(save_img, ((img[0],name,lock)))
                        IMGCOUNTER += 1
                        break
        while(lock[0] != thread_number):
            time.sleep(0.5)
            pass
        speed = IMGCOUNTER/((time.time() - STARTTIME) / 60)
        print "\ndone_page |%s|\t(%d|%d)\t|%s|\tspeed:%d pics/min"%(page_url,i,page_number,time.ctime(),speed)
            
        
def load_progress():
    if(os.path.exists('progress.txt')):
        fp_progress = open('progress.txt','r')
        return string.atoi(fp_progress.readline())
    return 1

def save_progress(progress):
    fp_progress = open('progress.txt','w')
    fp_progress.write("%d"%(progress))

def main():
    global IMGCOUNTER
    global STARTTIME
    STARTTIME = time.time()
    IMGCOUNTER = 0
    page_list_arr = load_page_list_file()
    line_number = 1
    start_page = load_progress()
    for photo_page in page_list_arr:
        if(start_page > line_number):
            line_number += 1
            continue
        print "start line_number %d :%s"%(line_number, photo_page)
        page_number = get_page_number(photo_page)
        download_img(photo_page,page_number)
        save_progress(line_number)
        line_number += 1

if __name__ == '__main__':
    main()
