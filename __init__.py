import requests as r
import browser_cookie3
import time
import threading

# wonderstruck is enchanting!

class Mainframe:
    def __init__(self):
        self.course_list = []
        self.dep_list = []
        self.cj = browser_cookie3.chrome(domain_name='sis.stolaf.edu')
        self.h = {
            "Host" : "sis.stolaf.edu",
            "Connection" : "keep-alive",
            "Origin" : "https://sis.stolaf.edu",
            "Accept-Encoding": "gzip, deflate, br",
        }
        self.user_classes = []
        self.username = ""
        self.setup()

    def setup(self):
        if not self.check_cookies():
            print("-----------------------\ncookie error! ensure that you're signed into SIS on chrome.\n-----------------------")
            return
        self.welcome()
        self.parse_classes()
        self.update_dep_codes()
        print("mainframe built.")

    def welcome(self):
        print ("""
                          _               _                   _    
                         | |             | |                 | |   
 __      _____  _ __   __| | ___ _ __ ___| |_ _ __ _   _  ___| | __
 \ \ /\ / / _ \| '_ \ / _` |/ _ \ '__/ __| __| '__| | | |/ __| |/ /
  \ V  V / (_) | | | | (_| |  __/ |  \__ \ |_| |  | |_| | (__|   < 
   \_/\_/ \___/|_| |_|\__,_|\___|_|  |___/\__|_|   \__,_|\___|_|\_\
                                                                              
                                                                          """)

        print("hello, {}\n".format(self.username))
        

    def parse_classes(self):
        print("building course list.")
        raw_class_list = r.get(search_url, headers=self.h, cookies=self.cj).text
        lines = raw_class_list.splitlines()
        for i in range(len(lines)):
            if '                        <td class="sis-left sis-deptnum" valign="top">' in lines[i]:
                dep_num_line = lines[i]
                dep = (dep_num_line.split(">")[1]).split("&")[0]
                num = (dep_num_line.split(";")[1]).split("<")[0]

                sec_line = lines[i+1]
                sec = (sec_line.split(">")[1]).split("<")[0]
                if sec == "":
                    sec = "0"
                
                id_name_line = lines[i+8]
                c_id = (id_name_line.split("clbid=")[1]).split('"')[0]
                name = (id_name_line.split('">')[1]).split("<")[0]

                # search variable line distance to find capacity
                # bug: lab classes are weird.
                capacity = ""
                for k in range(25,40):
                    if '<td class="sis-center" valign="top" style="white-space: nowrap;">' in lines[i+k]:
                        capacity = (lines[i+k+2].split(">")[1]).split("<")[0]                                                                

                new_course = Course(dep, num, sec, c_id, name, capacity)
                self.course_list.append(new_course)
        print("found {} classes.".format(len(self.course_list)))

    def update_dep_codes(self):
        for c in self.course_list:
            if c.dep not in self.dep_list:
                self.dep_list.append(c.dep)

    # true if cookies are properly configured
    def check_cookies(self):
        attempts = 1
        while attempts < 6:
            print("attempt #{} checking cookies...".format(attempts),end="")
            lines = (r.get(index_url, headers=self.h, cookies=self.cj).text).splitlines()

            for i in range(len(lines)):
                if "Signed in as" in lines[i]:
                    self.username = lines[i+1].strip()
                    print("success")
                    return True

            print("failed")
            time.sleep(2)
            self.update_cookies()
            attempts += 1
        return False

    def update_cookies(self):
        self.cj = browser_cookie3.chrome(domain_name='sis.stolaf.edu')

    def print_course_list(self, dep="", notfull=0):
        if notfull:
            for c in self.course_list:
                if not c.capacity:
                    continue
                nums = c.capacity.split('/')
                if int(nums[0]) < int(nums[1]):
                    print(c)
        else:
            for c in self.course_list:
                if dep == "" or dep == c.dep:
                    print(c)

    def choose_classes(self):
        print("\nUse dep_name class_num section (enter 0 if only 1 section) format\nExample: SOAN 121 0\nEnter q to stop\n")
        while True:
            usr = input("Enter the class you want: ").split()
            
            try:
                if usr[0].upper() == "Q":
                    break
                if usr[0].upper() == "NOTFULL":
                    self.print_course_list(notfull=1)
                    continue
                if usr[0].upper() == "ALL":
                    self.print_course_list()
                    continue

                dep = usr[0].upper()
                num = usr[1]
                sec = usr[2]
                if sec != "0":
                    sec = sec.upper()   
            except:
                print("\nbad input. Example: SOAN 121 0\n")
                continue

            if dep not in self.dep_list:
                print("bad dept! avaliable dept codes: {}\n".format(self.dep_list))
                continue

            found = False
            for c in self.course_list:
                if c.dep == dep and c.num == num and c.sec == sec:
                    self.user_classes.append(c)
                    print("added {} to your schedule!".format(c.name))
                    found = True
            if not found:
                print("course not found. available {} classes:".format(dep))
                self.print_course_list(dep)

    def run_req(self, url):
        response = r.post(url, headers=self.h, data=c.gen_add_data(), cookies=self.cj).text
        self.parse_response(response, c)
        

    def send_post_requests(self, times=1):
        for i in range(times):
            print("\nattempt #{}\n-----------------------".format(i+1))            
            for c in self.user_classes:
                print("sending ADD request for {}".format(c.name))
                #response = r.post(url, headers=self.h, data=c.gen_add_data(), cookies=self.cj).text
                #self.parse_response(response, c)
                #print(response)
                threading.Thread(target=run_req, args=(url, self.h, c.gen_add_data(), self.cj)).start()

    def parse_response(self, response, course):
        lines = response.splitlines()
        if len(lines) > 400:
            print("{} added successfully!".format(course.name))
            return
        
        error_list = {
            'You have already registered for this course' : "ERROR: Already registered.",
            'You have already taken this course the maximum number' : "ERROR: Are you in another section?",
            'This course or an attached required course has a time conflict' : "ERROR: Time conflict.",
            'You do not meet the prerequisites for this course': "ERROR: Unmet prerequisites.",
            'Selected class is now full' : "ERROR: Class full.",
            'There are no remaining' : "ERROR: There are no seats left for your class year.",
            "Error: the required form field 'attached_course_lab_select' was not found" : "ERROR: Lab classes not yet supported.",
            'Adding this course will cause you to exceed the maximum number of credits' : "ERROR: Exceeds credit limit.",
            'Error: Invalid grading type' : "ERROR: P/N classes not yet supported."
        }

        for e in error_list:
            if e in response:
                print(error_list[e] + "\n")


# this is a helper function to make the requests without waiting
# for a response via the "threading.Thread" line in send_post_requests()
def run_req(url, h, d, c):
    r.post(url, headers=h, data=d, cookies=c)
           
class Course:
    def __init__(self, dep, num, sec, c_id, name, cap):
        self.dep = dep
        self.num = num
        self.sec = sec
        self.c_id = c_id
        self.name = name
        self.capacity = cap

    def gen_add_data(self):
        return {
            "submit" : "add",
            "classlab_id" : str(self.c_id),
            "variable_credits" : "N",
            "grading_type" : "G",
            "selected_year_term" : "20233"
        }

    def __str__(self):
        return "{:<30s} {:<10s} {} {}".format(self.name[:25], (self.dep + self.num), self.sec, self.capacity)

# urls to essential things, should be updated every semester
index_url = "https://sis.stolaf.edu/sis/index.cfm"
desc_url = "https://sis.stolaf.edu/sis/public-coursedesc.cfm?clbid="
#url = "https://sis.stolaf.edu/sis/st-registration-interim.cfm"
url = "https://sis.stolaf.edu/sis/st-registration-spring.cfm"

#search_url = "https://sis.stolaf.edu/sis/st-registration-interim.cfm?searchinstructionmode=S&submit=Search#search_results"
search_url = "https://sis.stolaf.edu/sis/st-registration-spring.cfm?searchinstructionmode=S&submit=Search#search_results"


def main():
    mf = Mainframe()
    mf.choose_classes()    
    mf.send_post_requests(500)
    print("done!")

if __name__ == "__main__":
    main()
