# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 02:20:31 2020

@author: Krish Naik
"""

# -*- coding: utf-8 -*-
"""
Created on Fri May 15 12:50:04 2020

@author: krish.naik
"""

from apiclient.discovery import build
import numpy as np
import pickle
import pandas as pd
#from flasgger import Swagger
import streamlit as st 

from PIL import Image

#app=Flask(__name__)
#Swagger(app)

pickle_in = open("classifier.pkl","rb")
classifier=pickle.load(pickle_in)

def scrape_comments_with_replies():
        st.subheader("Input Video ID YouTube")
        ID = st.text_input(label='ID')
        if st.button("Enter"):
            api_key = "AIzaSyCNA7RgurTeVuiT7svjLXRXRJBXs1JWNAg"
            youtube = build("youtube", "v3", developerKey=api_key)
            box = [["Nama", "Komentar", "Waktu", "Likes", "Reply Count"]]
            data = youtube.commentThreads().list(part="snippet", videoId=ID, maxResults="100", textFormat="plainText").execute()

            for i in data["items"]:

                name = i["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                comment = i["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                published_at = i["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                likes = i["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                replies = i["snippet"]["totalReplyCount"]

                box.append([name, comment, published_at, likes, replies])

                totalReplyCount = i["snippet"]["totalReplyCount"]

                if totalReplyCount > 0:

                    parent = i["snippet"]["topLevelComment"]["id"]

                    data2 = youtube.comments().list(part="snippet", maxResults="100", parentId=parent,
                                                    textFormat="plainText").execute()

                    for i in data2["items"]:
                        name = i["snippet"]["authorDisplayName"]
                        comment = i["snippet"]["textDisplay"]
                        published_at = i["snippet"]["publishedAt"]
                        likes = i["snippet"]["likeCount"]
                        replies = ""

                        box.append([name, comment, published_at, likes, replies])

            while ("nextPageToken" in data):

                data = youtube.commentThreads().list(part="snippet", videoId=ID, pageToken=data["nextPageToken"],
                                                    maxResults="100", textFormat="plainText").execute()

                for i in data["items"]:
                    name = i["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                    comment = i["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    published_at = i["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                    likes = i["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                    replies = i["snippet"]["totalReplyCount"]

                    box.append([name, comment, published_at, likes, replies])

                    totalReplyCount = i["snippet"]["totalReplyCount"]

                    if totalReplyCount > 0:

                        parent = i["snippet"]["topLevelComment"]["id"]

                        data2 = youtube.comments().list(part="snippet", maxResults="100", parentId=parent,
                                                        textFormat="plainText").execute()

                        for i in data2["items"]:
                            name = i["snippet"]["authorDisplayName"]
                            comment = i["snippet"]["textDisplay"]
                            published_at = i["snippet"]["publishedAt"]
                            likes = i["snippet"]["likeCount"]
                            replies = ""

                            box.append([name, comment, published_at, likes, replies])

            df = pd.DataFrame({"Nama": [i[0] for i in box], "Komentar": [i[1] for i in box], "Waktu": [i[2] for i in box],
                            "Likes": [i[3] for i in box], "Reply Count": [i[4] for i in box]})

            df.to_csv("YouTube-Komentar.csv", index=False, header=False)
            df.shape
            st.success('Komentar Youtube Berhasil Discrape!')

#@app.route('/')
def welcome():
    return "Welcome All"

#@app.route('/predict',methods=["Get"])
def predict_note_authentication(variance,skewness,curtosis,entropy):
    
    """Let's Authenticate the Banks Note 
    This is using docstrings for specifications.
    ---
    parameters:  
      - name: variance
        in: query
        type: number
        required: true
      - name: skewness
        in: query
        type: number
        required: true
      - name: curtosis
        in: query
        type: number
        required: true
      - name: entropy
        in: query
        type: number
        required: true
    responses:
        200:
            description: The output values
        
    """
   
    prediction=classifier.predict([[variance,skewness,curtosis,entropy]])
    print(prediction)
    return prediction



def main():
    activities = st.sidebar.selectbox("Pilih Menu",( "Input Video ID YouTube","Analisa Sentimen Komentar","Tentang"))
    if activities == "Input Video ID YouTube":
        scrape_comments_with_replies()
    st.title("Bank Authenticator")
    html_temp = """
    <div style="background-color:tomato;padding:10px">
    <h2 style="color:white;text-align:center;">Streamlit Bank Authenticator ML App </h2>
    </div>
    """
    st.markdown(html_temp,unsafe_allow_html=True)
    variance = st.text_input("Variance","Type Here")
    skewness = st.text_input("skewness","Type Here")
    curtosis = st.text_input("curtosis","Type Here")
    entropy = st.text_input("entropy","Type Here")
    result=""
    if st.button("Predict"):
        result=predict_note_authentication(variance,skewness,curtosis,entropy)
    st.success('The output is {}'.format(result))
    if st.button("About"):
        st.text("Lets LEarn")
        st.text("Built with Streamlit")

if __name__=='__main__':
    main()
