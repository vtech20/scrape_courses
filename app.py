from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import json
import pymongo
import sys
import traceback

app = Flask(__name__)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/scrape',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            url = "https://courses.ineuron.ai/"
            uClient = requests.get(url)
            ineuron_html = bs(uClient.content, "html.parser")
            scrap_data = ineuron_html.find_all('script')[14].text.strip()
            json_data = json.loads(scrap_data)
            init_courses = json_data['props']['pageProps']['initialState']['filter']['initCourses']
            instructor_details = json_data['props']['pageProps']['initialState']['init']['instructors']
            inst_dict = {}
            for keys, values in instructor_details.items():
                inst_dict[keys] = values['name']
            extracts = []
            for idx,i in enumerate(init_courses[0:50]):
                extract_dict = {}
                extract_dict['course_name'] = init_courses[idx]['title']
                extract_dict['course_description'] = init_courses[idx]['description']
                course_nam = init_courses[idx]['title']
                course_nam = course_nam.replace(" ","-")
                int_url = "https://courses.ineuron.ai/" + course_nam
                internal_level = requests.get(int_url)
                ineuron_int_level = bs(internal_level.content, "html.parser")
                scrap_data1 = ineuron_int_level.find_all('script')[12].text.strip()
                json_data1 = json.loads(scrap_data1)
                sample_dict = json_data1['props']['pageProps']['data']
                if 'meta' in sample_dict.keys():
                    instuc = json_data1['props']['pageProps']['data']['meta']['instructors']
                    instructor_name = [inst_dict[i] for i in instuc]
                    extract_dict['instructors'] = ",".join(instructor_name)
                    curriculam = json_data1['props']['pageProps']['data']['meta']['curriculum']
                    curricul_list = []
                    for keys,values in curriculam.items():
                        curricul_list.append(curriculam[keys]['title'])
                        
                    extract_dict['Curriculam'] = ",".join(curricul_list)
                    requirements = json_data1['props']['pageProps']['data']['meta']['overview']['requirements']
                    extract_dict['Requirements'] = ",".join(requirements)
                    features = json_data1['props']['pageProps']['data']['meta']['overview']['features']
                    extract_dict['Course_Features'] = ",".join(features)
                    pricing = json_data1['props']['pageProps']['data']['details']['pricing']
                    if 'IN' in pricing.keys():
                        extract_dict['Price'] = json_data1['props']['pageProps']['data']['details']['pricing']['IN']
                    elif 'isFree' in pricing.keys():
                        extract_dict['Price'] = 'Free'
                else:
                    val = json_data1['props']['pageProps']['data']['batches']
                    for keys,values in val.items():
                        instuc = values['meta']['instructors']
                        instructor_name = [inst_dict[i] for i in instuc]
                        extract_dict['instructors'] = ",".join(instructor_name)
                        curriculam = values['meta']['curriculum']
                        curricul_list = []
                        for keys1,values1 in curriculam.items():
                            curricul_list.append(curriculam[keys1]['title'])
                        extract_dict['Curriculam'] = ",".join(curricul_list)
                        requirements = values['meta']['overview']['requirements']
                        extract_dict['Requirements'] = ",".join(requirements)
                        features = values['meta']['overview']['features']
                        extract_dict['Course_Features'] = ",".join(features)
                        pricing = values['batch']['pricing']
                        if 'IN' in pricing.keys():
                            extract_dict['Price'] = pricing['IN']
                        elif 'isFree' in pricing.keys():
                            extract_dict['Price'] = 'Free'
                extracts.append(extract_dict)
         
            mongo_connection_string = "mongodb+srv://mongodb:mongodb@cluster0.xs8xl.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
            client = pymongo.MongoClient(mongo_connection_string)
            db = client.test
            collection = db['ineuron_courses_collection']
            collection.insert_many(extracts)
            print(f'inserted {len(extracts)} extracts')
            
            
            return render_template('results.html', extracts=extracts[0:(len(extracts)-1)])
        except Exception as e:
            print('The Exception message is: ',e)
            print(traceback.format_exc())
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8001, debug=True)
	#app.run(debug=True)
