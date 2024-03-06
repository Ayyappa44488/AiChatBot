import streamlit as st
import google.generativeai as genai
import PIL.Image
import speech_recognition as sr
from streamlit_option_menu import option_menu
import re
import pyttsx3
import fitz
from docx import Document
import csv
from io import StringIO
import mysql.connector
import datetime
from email.message import EmailMessage
import smtplib
import ssl
GOOGLE_API_KEY='your key'
conn=mysql.connector.connect(host="localhost",user="root",password="",database="chatbot")
cursor = conn.cursor(dictionary=True) 
email_sender = 'your mail'
email_password = 'your password'
def send_mail(mail,body):
    subject = 'Mail from kiosk'
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = mail
    em['Subject'] = subject
    em.set_content(body,subtype="html")
    context = ssl.create_default_context()
    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender,mail, em.as_string())
    return
def read_csv(upload_file):
    try:
        file_content = upload_file.read()

        # Decode the bytes content assuming it's in UTF-8
        decoded_content = file_content.decode('utf-8')

        # Use the CSV module to read the data
        csv_reader = csv.reader(decoded_content.splitlines())

        # Use StringIO to write the CSV data to a string
        csv_string_io = StringIO()
        csv_writer = csv.writer(csv_string_io)

        for row in csv_reader:
            csv_writer.writerow(row)

        # Get the CSV string
        csv_string = csv_string_io.getvalue()

        return csv_string

    except Exception as e:
        print(f"Error: {e}")
        return None
def read_txt(uploaded_file):
    try:
        text = uploaded_file.read().decode('utf-8')
        print(text)
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        uploaded_file.close()
def read_docx(file_path):
    doc = Document(file_path)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)
def read_pdf(uploaded_file):
    try:
        # Assuming 'uploaded_file' is a file-like object in memory

        # Use PyMuPDF (fitz) to read the PDF content
        doc = fitz.open("pdf", uploaded_file.read())
        text = ""

        for page in doc:
            text += page.get_text("text") + "\n"  # Extract plain text

        doc.close()
        return text

    except Exception as e:
        print(f"Error: {e}")
        return None

def process_text(text):
    genai.configure(api_key=GOOGLE_API_KEY)
    # img = PIL.Image.open('7989259929.png')

    model = genai.GenerativeModel('gemini-pro')
    # response = model.generate_content(img)
    response = model.generate_content(text)
    print(response.text)
    return response.text.lower()

def process_image(image,text):
    genai.configure(api_key=GOOGLE_API_KEY)
    img = PIL.Image.open(image)

    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([text,img])
    response.resolve()
    print(response.text)
    return response.text.lower()
def mail_check(text):
  text=text.lower()
  text1=text.split()
  keyword = ["that","saying","say","composing","compose","message:","message","content:"]
  content=""
  if "mail" or "email" or "gmail" and "send" or "draft" or "craft" in text1:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    if matches:
      for i in keyword:
        if i in text:
          index=text.index(i)+len(i)
          content=text[index:]
          break
      if not content:
        i=text.find(matches[0])+len(matches[0])
        content=text[i:]
    content=content.strip()
    return matches,content
  else:
    return False
def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return
def display():
  for message in st.session_state["chat_history"]:
    if message["is_user"]:
      dim_text =f"<span style='background-color: yellow;'>You: \n{message['user']}</span>"
      st.write(dim_text, unsafe_allow_html=True)
    else:
      highlight_text = f"<span style='color: grey;'>Bot:\n{message['bot']}</span>"
      st.write(highlight_text, unsafe_allow_html=True)
  return
def display_recent():
  for message in st.session_state["recent_history"]:
    if message["is_user"]:
      dim_text =f"<span style='background-color: yellow;'>You: \n{message['user']}</span>"
      st.write(dim_text, unsafe_allow_html=True)
    else:
      highlight_text = f"<span style='color: grey;'>Bot:\n{message['bot']}</span>"
      st.write(highlight_text, unsafe_allow_html=True)
  return
# Chat history (stored in session state)
def main():
  if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
  if "recent_history" not in st.session_state:
    st.session_state["recent_history"] = []
  if "login" not in st.session_state:
    st.session_state.login = False
  # if "content" not in st.session_state:
  #   st.session_state.content=""
  with st.sidebar:
    selected=option_menu("Bot",["login","chatbot","voicebot"])
  if selected=="chatbot" and "login" in st.session_state and st.session_state.login==True:
    sql="select date from data where email=%s group by date"
    val=(st.session_state.email,)
    cursor.execute(sql,val)
    result=cursor.fetchall()
    dates=["previous"]
    for i in result:
      dates.append(str(i['date']))
    chatbot_options = st.sidebar.selectbox("Previous Chats", dates)
    if "user_name" in st.session_state:
          st.sidebar.write("Welcome",st.session_state.user_name)
          logout=st.sidebar.button("logout")
    st.title("Chat with ChatBOT")
    text_input = st.text_input("Type your message here...")
    uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=False)
    search=st.button("click me")
    if chatbot_options != "previous":
      sql="select * from data where email=%s and date=%s"
      val=(st.session_state.email,chatbot_options)
      cursor.execute(sql,val)
      result=cursor.fetchall()
      print(len(result))
      st.session_state["recent_history"]=[]
      for i in result:
          recent_chat=i['question']+'\n'+i['response']
          if i['question']!=None:
            st.session_state["recent_history"].insert(0,{"user": i['question'], "is_user": True})
          if i['response']!=None:
            st.session_state["recent_history"].insert(1,{"bot": i['response'], "is_user": False})
      display_recent()
    if search:
      mail,content=mail_check(text_input)
      st.session_state["mail"]=mail
      if mail:
        # st.write("Do you want to send mail to",mail[0])
        # text=st.text_area("content")
        # print(text)
        # st.session_state.content=text
        # send_email=st.button("send mail")
        if content:
          with st.spinner("sending..."):
              send_mail(mail[0],content)
          st.success("mail sent successfully")
        else:
          st.error("unable to send the prompt")
      else:
        st.session_state["chat_history"].insert(0,{"user": text_input, "is_user": True})
        if uploaded_file is not None:
          file_extension = uploaded_file.name.split(".")[-1].lower()
          if file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg"]:
            with st.spinner("processing..."):
              response = process_image(uploaded_file,text_input)
          elif file_extension=="pdf":
            text=read_pdf(uploaded_file)
            total_text=text_input+"\n"+text
            with st.spinner("processing..."):
              response = process_text(total_text)
          elif file_extension=="docx":
            text=read_docx(uploaded_file)
            total_text=text_input+"\n"+text
            with st.spinner("processing..."):
              response = process_text(total_text)
          elif file_extension=="txt":
            text=read_txt(uploaded_file)
            total_text=text_input+"\n"+text
            with st.spinner("processing..."):
              response = process_text(total_text)
          elif file_extension=="csv":
            text=read_csv(uploaded_file)
            total_text=text_input+"\n"+text
            with st.spinner("processing..."):
              response = process_text(total_text)
          else:
            response = "uploaded file non type of image or pdf"
        else: 
          text=text_input
          if chatbot_options!="previous":
            text=recent_chat+'\n'+text_input
          with st.spinner("processing..."):
            response = process_text(text)
        # Add chatbot response to chat history
        mail=st.session_state.email
        date=datetime.datetime.now()
        sql="insert into data values(%s,%s,%s,%s)"
        val = (mail,text_input,response,date)
        cursor.execute(sql, val)
        conn.commit()  
        st.session_state["chat_history"].insert(1,{"bot": response, "is_user": False})
        display()
  elif selected=="voicebot"  and "login" in st.session_state and st.session_state.login==True:
    st.title("Talk with VoiceBOT")
    talk=st.button("talk")
    if "user_name" in st.session_state:
          st.sidebar.write("Welcome",st.session_state.user_name)
          logout=st.sidebar.button("logout")
    if talk:
      r=sr.Recognizer()
      with sr.Microphone() as source:
        st.write("listening")
        audio=r.listen(source)
        try:
          with st.spinner("recognizing"):
              text=r.recognize_google(audio)
              # st.write("listening")
              # audio=r.listen(source)
              # st.write("recognizing")
              # text=r.recognize_google(audio)
          print("you said:{}".format(text))
          mail=mail_check(text)
          if mail:
            st.write("Do you want to send mail to",mail[0])
          else:
            # if text=="stop":
            #   break
            with st.spinner("processing"):
              response = process_text(text)
            response=response.replace("*","")
            st.session_state["chat_history"].append({"user": text, "is_user": True})
            st.session_state["chat_history"].append({"bot": response, "is_user": False})
            display()
            text_to_speech(response)
        except:
            st.write("Sorry could not recognize what you said")
            print("Sorry could not recognize what you said")
  else:
    sb="""
    <style>
    [class="css-vk3wp9 e1fqkh3o11"]{
    background-image: linear-gradient(to right bottom,pink,violet,#87cefa);
    }
    </style>"""
    log="""
    <style>
    [class="main css-uf99v8 egzxvld5"]{
        background-image: linear-gradient(to right bottom,#FFFFFF,#87CEEB);
    }
    </style>"""
    st.markdown(log,unsafe_allow_html=True)
    st.markdown(sb,unsafe_allow_html=True)
    # def make_hashes(password):
    #     return hashlib.sha256(str.encode(password)).hexdigest()

    # def check_hashes(password,hashed_text):
    #     if make_hashes(password) == hashed_text:
    #         return hashed_text
    #     return False
    # import sqlite3 
    # conn = sqlite3.connect('data2.db')
    # c = conn.cursor()
    # # DB  Functions
    # def create_usertable():
    #     c.execute('CREATE TABLE IF NOT EXISTS user1table(username TEXT,password TEXT,email TEXT PRIMARY KEY,dob DATE,phone TEXT)')
    # def add_userdata(username,password,email,dob,phone):
    #     c.execute('INSERT INTO user1table(username,password,email,dob,phone) VALUES (?,?,?,?,?)',(username,password,email,dob,phone))
    #     conn.commit()

    # def login_user(email,password):
    #     c.execute('SELECT * FROM user1table WHERE email =? AND password = ?',(email,password))
    #     data = c.fetchall()
    #     return data
    # def already(email,phone):
    #     c.execute('SELECT * FROM user1table WHERE email =? OR phone= ?',(email,phone))
    #     data = c.fetchall()
    #     return data
    # def view_all_users():
    #     c.execute('SELECT * FROM user1table')
    #     data = c.fetchall()
    #     return data
    # import datetime
    select=st.selectbox("Login/Signup",options=("Login","Signup"))
    if select=="Login":
        st.subheader("Login Section")
        mail = st.text_input("Email")
        password = st.text_input("Password",type='password')
        if st.button("Login"):
                sql = "SELECT * FROM register WHERE email = %s and password=%s"
                condition_value = (mail,password)
                # Execute the SQL query with the provided condition
                cursor.execute(sql, condition_value)
                # Fetch the result (in this case, a single integer representing the count)
                result = cursor.fetchall()
                if len(result)==1:
                    for i in result:
                        name1=i['name']
                    st.session_state.user_name=name1
                    st.session_state.login=True
                    st.session_state.email=mail
                    st.balloons()
                    st.success("login successfull")
                else:
                  st.warning("Invalid Credentials")
        if "user_name" in st.session_state:
          st.sidebar.write("Welcome",st.session_state.user_name)
          logout=st.sidebar.button("logout")
          if logout:
            st.session_state.pop("login")
            st.session_state.pop("user_name")
    if select=="Signup":
        st.subheader("Create New Account")
        new_user = st.text_input("Name")
        new_password = st.text_input("Strong_Password",type='password')
        new_email = st.text_input("Email")
        new_phone=st.text_input("Phone",max_chars=10)
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if st.button("Signup"):
            if len(new_password)<6 or not re.fullmatch(regex,new_email) or len(new_phone)<10:
                st.error('please fill details correctly')
            else: 
                sql="select * from register where email=%s"
                val=(new_email,)
                cursor.execute(sql,val)
                result=cursor.fetchall()
                if len(result)==1:
                    st.warning('Already had an account/please login')
                else:
                    sql = "INSERT INTO register VALUES (%s,%s, %s,%s)"
                    val = (new_email,new_password,new_user,new_phone)
                    cursor.execute(sql, val)
                    conn.commit()  
                    st.success("You have successfully created a valid Account")
                    st.info("Go to Login Menu to login")


                      
if __name__ == "__main__":
    main()