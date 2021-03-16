import os,sklearn,plotly.express as px, pandas as pd, nltk,re,string,streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score,f1_score,recall_score,accuracy_score,confusion_matrix,classification_report #evaluasi performa model
from sklearn.feature_extraction.text import TfidfVectorizer
from google_trans_new import google_translator
from apiclient.discovery import build
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import numpy as np
import pickle
import pandas as pd
import streamlit as st 

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

def preprocessing ():
        st.info('Proses Preprocessing....')
        # ------ Case Folding ---------
        df = pd.read_csv('./YouTube-Komentar.csv')
        def case_f(text):
                #remove tab, new line, ans back slice
                text = text.replace("\\t"," ").replace("\\n"," ").replace("\\u"," ").replace("\\","")
                #remove non ASCII (emoticon, chinese word, .etc)
                text = text.encode("ascii", "replace").decode("ascii")
                #remove mention, link, hashtag
                text = " ".join(re.sub("([@#][A-Za-z0-9]+)|(\w+:\/\/\S+)"," ", text).split())
                #remove incomplete URL
                text= text.replace("http://", " ").replace("https://", " ")
                #remove number
                text = re.sub(r"\d+", "", text)
                #remove punctuation/tanda baca
                text = text.translate(str.maketrans("","",string.punctuation))
                #remove whitespace leading & trailing/ spasi
                text = text.strip()
                #remove multiple whitespace into single whitespace
                text = re.sub("\s+"," ",text)
                return text
        df["Komentar_Case_Folding"] = df["Komentar"].apply(case_f)

        # ------ Sentence Tokenized ---------
        def sentence_tokenized(text):
                return sent_tokenize(text)

        df["Komentar_Sentence_Tokenized"] = df["Komentar_Case_Folding"].apply(sentence_tokenized)


        # ------ Word Tokenize ---------
        def word_tokenize_wrapper(text):
            return word_tokenize(text)

        df["Komentar_Word_Tokenizing"] = df["Komentar_Case_Folding"].apply(word_tokenize_wrapper)
        
        #-- PERBAIKAN KATA TIDAK BAKU --

        normalized_word = pd.read_excel("./NormalisasiKata.xlsx")

        normalized_word_dict = {}

        for index, row in normalized_word.iterrows():
            if row[0] not in normalized_word_dict:
                normalized_word_dict[row[0]] = row[1] 

        def normalized_term(text):
            return [normalized_word_dict[term] if term in normalized_word_dict else term for term in text]

        df["Komentar_Normalisasi"] = df["Komentar_Word_Tokenizing"].apply(normalized_term)

        #--------Stopwords--------
        stop_words=stopwords.words("indonesian")
        stop_words.extend(["yg","dg","rt","dgn","mkn","nya","ny","d","klo","kalo",
                        "&amp","biar","bikin","bilang","gak","ga","krn","nya","nih",
                        "sih","si","tau","tdk","tuh","utk","ya","jd","jgn","sdh",
                        "aja","n","t","nyg","hehe","pen","u","nan","loh","rt",
                        "yah","gw","kak","yang", "untuk", "pada", "ke", "para", "namun",
                        "menurut", "antara", "dia", "dua", "ia", "seperti", "jika", "jika",
                        "sehingga", "kembali", "dan", "ini", "karena", "kepada", 
                        "oleh", "saat", "harus", "sementara", "setelah", "belum", "kami", 
                        "sekitar", "bagi", "serta", "di", "dari", "telah", "sebagai", 
                        "masih", "hal", "ketika", "adalah", "itu", "dalam", "bisa", "bahwa",
                        "atau", "hanya", "kita", "dengan", "akan", "juga", "ada", "mereka",
                        "sudah", "saya", "terhadap", "secara", "agar", "lain", "anda", "begitu",
                        "mengapa", "kenapa", "yaitu", "yakni", "daripada", "itulah", "lagi", 
                        "maka", "tentang", "demi", "dimana", "kemana", "pula", "sambil", "sebelum",
                        "sesudah", "supaya", "guna", "kah", "pun", "sampai", "sedangkan", "selagi", 
                        "sementara", "tetapi", "apakah", "kecuali", "sebab", "selain", "seolah",
                        "seraya", "seterusnya", "tanpa", "agak", "boleh", "dapat", "dsb", "dst", 
                        "dll", "dahulu", "dulunya", "anu", "demikian", "tapi", "ingin", "juga",
                        "nggak", "mari", "nanti", "melainkan", "oh", "ok", "seharusnya", 
                        "sebetulnya", "setiap", "setidaknya", "sesuatu", "pasti", "saja",
                        "toh", "ya", "walau", "tolong", "tentu", "amat", "apalagi", "bagaimanapun",
                        "adalah","akan","akhir","aku","saya","antara","antaranya","apabila","atau",
                        "bahwa","bahwasannya","berikut","berkata","berupa","dan","dalam","dapat",
                        "dari","demikian","dengan","di","dia","beliau","mas","pak","diri","dirinya",
                        "guna","hal","hingga","ia","ialah","ibarat","ibaratnya","ibu","ingin",
                        "inginkan","ini","itu","jadi","kami","kalian","kamu","kan","karena","kini",
                        "lalu","kita","maka","mereka","merupakan","misal","misalkan","misalnya","pertama",
                        "orang","pada","nya","saat","sendiri","sini","yaitu","yang","kalau","jika","untuk",
                        "secara","sedangkan","luar","alangkah","wkkk",
                        "wkwkw","wkwkwkw","wk","wkkw","mbak","mbk","cece","cici","ci","ce","kk"])
        stop_words.remove("tidak")
        list_stopwords = set(stop_words)

        #--------Stemmer--------
        def stopwords_removal(text):
                return [word for word in text if word not in list_stopwords]

        df["Komentar_Filter"] = df["Komentar_Normalisasi"].apply(stopwords_removal)

        # create stemmer
        factory = StemmerFactory()
        stemmer = factory.create_stemmer()

        # stemmed
        def stemmed_wrapper(term):
            return stemmer.stem(term)

        term_dict = {}
        for document in df["Komentar_Filter"]:
            for term in document:
                if term not in term_dict:
                    term_dict[term] = " "

        for term in term_dict:
            term_dict[term] = stemmed_wrapper(term)
                    
        # apply stemmed term to dataframe
        def get_stemmed_term(text):
            return [term_dict[term] for term in text]

        df["Komentar_Stemmer"] = df["Komentar_Filter"].apply(get_stemmed_term)

        #--------Translate--------
        translator = google_translator()
        df["Komentar_Translate"] = df["Komentar_Stemmer"].apply(translator.translate, lang_src="id", lang_tgt="en")

        nilai = SentimentIntensityAnalyzer()
        data_label = df["Komentar_Translate"]
        def get_sentiment(Komentar_Translate):
            vader_scores = nilai.polarity_scores(Komentar_Translate)
            compound_score = vader_scores["compound"]
            if (compound_score >= 0.05):
                return "Positif"
            elif (compound_score < 0.05 and compound_score > -0.05):
                return "Netral"
            elif (compound_score <= -0.05):
                return "Negatif"
        vader_sentiments = df.Komentar_Translate.apply(get_sentiment)

        df['Label'] = vader_sentiments
        df.to_csv("Hasil-Akhir.csv")

        df_akhir =pd.concat([df["Komentar"],df["Komentar_Case_Folding"],df["Komentar_Sentence_Tokenized"],
        df["Komentar_Word_Tokenizing"],df["Komentar_Normalisasi"],df["Komentar_Filter"],df["Komentar_Stemmer"],
        df['Label']],axis=1)
        st.subheader("Hasil Preprocessing Data")
        st.dataframe(df_akhir)
        
        st.subheader("Hasil")
        sentiment_count = df['Label'].value_counts()
        Sentiment_count = pd.DataFrame({'Label' :sentiment_count.index, 'Jumlah' :sentiment_count.values})
        st.write(Sentiment_count)

        df_data = df[df["Label"] == "Netral"].index
        df.drop(df_data, inplace=True)

        max_features = 2500
        data_klasifikasi= df["Komentar_Translate"].astype(str)

        #menambahkan ngram=(1,2) dst kalo mau pake pemisahan per 2 kata atau lebih
        tfidf = TfidfVectorizer(max_features=max_features, ngram_range=(1,3), smooth_idf=False)
        tfs = tfidf.fit_transform(data_klasifikasi)
        IDF_vector = tfidf.idf_

        # hitung TF x IDF sehingga dihasilkan TFIDF matrix / vector
        hasil_tfidf = tfidf.fit_transform(data_klasifikasi).toarray()
        X= hasil_tfidf
        Y= df["Label"]

        #splitting data
        X_train,X_test,Y_train,Y_test= train_test_split(X,Y,test_size=0.15,random_state=0)
        clasfc = MultinomialNB()
        cl = clasfc.fit(X_train,Y_train)
        Y_pred = cl.predict(X_test)
        st.subheader("Performa Analisis Komentar YouTube")
        st.write(f"Confusion Matrix", confusion_matrix(Y_test,Y_pred))
        st.write(f"Accuracy-Score: ", accuracy_score(Y_test, Y_pred))
        st.write(f"F1-Score", f1_score(Y_test,Y_pred,pos_label='Positif'))
        st.write(f"Precision-Score", precision_score(Y_test, Y_pred, average=None))
        st.write(f"Recall-Score", recall_score(Y_test,Y_pred,pos_label='Positif'))
        #st.write(f"Classification Rreport", classification_report(Y_test,Y_pred))
        
        st.write("Persentase Analisis Sentimen Komentar YouTube")
        sentiment_count = df['Label'].value_counts()
        sentiment_count = pd.DataFrame({'Sentiment' :sentiment_count.index, 'Label' :sentiment_count.values})
        fig = px.pie(sentiment_count, values='Label', names='Sentiment')
        st.plotly_chart(fig)

def loadpage(): 
            st.markdown('''
            <div>
                <!---<h1 class="title">Abstrak</h1>--->
                <p class="abstrak">
                Saat ini YouTube merupakan salah satu media sosial yang paling populer. 
                Hampir semua kalangan masyarakat saat ini menggunakan Youtube. Youtube 
                merupakan media sosial yang dapat digunakan untuk mengirim, melihat dan 
                berbagi video. Pengguna YouTube yang menonton video YouTube dapat 
                menyampaikan opininya melalui kolom komentar pada YouTube. Komentar yang 
                disampaikan dapat digunakan sebagai analisis pada video YouTube tersebut. Dari 
                analisis ini dapat dijadikan sebagai tolak ukur terhadap video yang dibuat untuk 
                mendapatkan feedback dari penonton, positif atau negatif. Untuk mengatasi 
                permasalahan klasifikasi komentar pengguna YouTube dirancanglah sebuah sistem 
                analisis komentar berdasarkan filter YouTube dengan algoritma Naïve Bayes. 
                Sistem analisis komentar pada YouTube yang dibuat akan menghasilkan klasifikasi 
                dari komentar-komentar pengguna YouTube dengan kategori positif dan negatif. 
                Sistem ini diharapkan dapat menjadi bahan evaluasi para konten kreator untuk 
                meningkatkan kualitas dari saluran YouTubenya.</p>
            </div>               
            ''',unsafe_allow_html=True)
            if st.checkbox("Tentang Penulis dan Pembimbing"):
                st.markdown('''
                <div id='container'>
                    <div id="conten">
                            <h2 class="title">Penulis</h2>
                        <p class="biodata">Nama : Mampe P Munthe
                        <br>Perguruan Tinggi : Universitas Telkom
                        <br>Program Studi : Teknik Komputer
                        <br>NIM : 1103198216
                        <br></p>
                    </div>
                </div>
                <div>
                    <div id='parent'>
                        <div id='wide'>
                            <h2 class="title">Pembimbing I</h2>
                            <p class="biodata1">Nama  : Anton Siswo Raharjo Ansori S.T., M.T. 
                            <br>NIP :  15870031</p>
                        </div>
                        <div id='narrow'>
                            <h2 class="title">Pembimbing II</h2>
                            <p class="biodata1">Nama : Dr. Reza Rendian Septiawan, S.Si., M.Si., M.Sc
                            <br>NIP : 20910011</p>
                        </div>
                    </div>
                </div>              
            ''',unsafe_allow_html=True)
            

def main():
    st.title("Analisis Sentimen Komentar Pada Saluran Youtube Food Vlogger Berbahasa Indonesia Menggunakan Algoritma Naïve Bayes")

    activities = st.sidebar.selectbox("Pilih Menu",( "Input Video ID YouTube","Analisa Sentimen Komentar","Tentang"))

    if activities == "Input Video ID YouTube":
        scrape_comments_with_replies()
        
    elif activities == "Analisa Sentimen Komentar":
        st.subheader("Data Komentar YouTube")
        file_csv_yt = ('./YouTube-Komentar.csv')
        if os.path.exists(file_csv_yt):
              df = pd.read_csv(file_csv_yt)
              st.subheader("Hasil Data Sebelumnya")
              st.dataframe(df)
        else:
              st.warning('''Maaf Data Komentar YouTube Belum Ada,
                    Lakukan Scrape Komentar Youtube Dulu''') 

        st.write("""=========================================================================""")
            
        if st.button("Lakukan Preprocessing"):
            preprocessing()

        if st.checkbox("Tampilkan Analisis Data Sebelumnya "):
            file_csv = ('./Hasil-Akhir.csv')
            if os.path.exists(file_csv):
                df = pd.read_csv(file_csv)
                df = pd.concat([df["Komentar"],df['Label']],axis=1)
                st.subheader("Hasil Data Sebelumnya")
                st.table(df)
                
                
            else:
               st.warning("""Maaf Data Belum Ada""") 

    else:
        loadpage() 

if __name__=='__main__':
    main()  
