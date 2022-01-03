import requests as r
import re
import browser_cookie3
import time
import pickle
from os.path import exists

# excise is grabs a class list creates a simple data structure containing
# all the class info with it

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
        self.setup()

    def setup(self):
        self.parse_classes()
        self.update_dep_codes()
        print("mainframe built.")

    def parse_classes(self):
        print("begin parse")
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

                new_course = Course(dep, num, sec, c_id, name)
                self.course_list.append(new_course)

    def update_dep_codes(self):
        for c in self.course_list:
            if c.dep not in self.dep_list:
                self.dep_list.append(c.dep)

    def update_cookies(self):
        self.cj = browser_cookie3.chrome(domain_name='sis.stolaf.edu')

    def print_course_list(self, dep=""):
        for c in self.course_list:
            if dep == "" or dep == c.dep:
                print(c)

    def choose_classes(self):
        print("Use dep_name class_num section (enter 0 if only 1 section) format\nExample: SOAN 121 0\nEnter q to stop\n")
        while True:
            usr = input("Enter the class you want: ").split()
            
            try:
                if usr[0].upper() == "Q":
                    break
                
                dep = usr[0].upper()
                num = usr[1]
                sec = usr[2]
                if sec != "0":
                    sec = sec.upper()
            except:
                print("bad input. Example: SOAN 121 0\n")
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

    def send_post_requests(self):
        for c in self.user_classes:
            response = r.post(url, headers=self.h, data=c.gen_add_data(), cookies=self.cj)
            print(response.text)
            
class Course:
    def __init__(self, dep, num, sec, c_id, name):
        self.dep = dep
        self.num = num
        self.sec = sec
        self.c_id = c_id
        self.name = name

    def gen_add_data(self):
        return {
            "submit" : "add",
            "classlab_id" : str(self.c_id),
            "variable_credits" : "N",
            "grading_type" : "G",
            "selected_year_term" : "20213"
        }

    def __str__(self):
        return "{:<30s} {:<10s} {}".format(self.name[:25], (self.dep + self.num), self.sec)

# urls to essential things, should be updated every semester
index_url = "https://sis.stolaf.edu/sis/index.cfm"
desc_url = "https://sis.stolaf.edu/sis/public-coursedesc.cfm?clbid="
url = "https://sis.stolaf.edu/sis/st-registration-spring.cfm"
search_url = "https://sis.stolaf.edu/sis/st-registration-spring.cfm?searchinstructionmode=S&submit=Search#search_results"

def main():
    mf = Mainframe()
    mf.choose_classes()
    mf.send_post_requests()

if __name__ == "__main__":
    main()
