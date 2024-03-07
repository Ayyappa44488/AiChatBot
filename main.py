#importing the required libraries
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
import io
GOOGLE_API_KEY='AIzaSyBeZTTzDcc3HSMIgo89exF8TJhrhsZtsnM'
conn=mysql.connector.connect(host="localhost",user="root",password="",database="chatbot")
cursor = conn.cursor(dictionary=True) 
#Email App Passwords
email_sender = 'kchinnareddy2016@gmail.com'
email_password = 'iawcyyplxaddxkdx'
def audio_to_text(uploaded_file):
#this method is used to convert audio to text
    recognizer = sr.Recognizer()

    # Check if a file was uploaded
    if uploaded_file is not None:
        try:
            # Get the content of the uploaded file as bytes
            audio_content = uploaded_file.read()

            # Convert audio content to a file-like object
            audio_file = io.BytesIO(audio_content)

            # Use the Google Web Speech API to transcribe the audio
            with sr.WavFile(audio_file) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio)
            return text

        except sr.UnknownValueError:
            st.error("Google Web Speech API could not understand audio")

        except sr.RequestError as e:
            st.error("Could not request results from Google Web Speech API; {0}".format(e))
    return None

def send_mail(mail,body):
#this method is used to send mail
    subject = 'Mail from ayyappa reddy'
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
#this method is used to read the csv file and convert it into string
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
#this method is used to read the text file
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
#this method is used to read a document
    doc = Document(file_path)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)
def read_pdf(uploaded_file):
#this method is used to read a pdf
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
#this an text based gemini model used to process the text
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(text)
    return response.text.lower()

def process_image(image,text):
#this an image based gemini model used to process the image and text
    genai.configure(api_key=GOOGLE_API_KEY)
    img = PIL.Image.open(image)

    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([text,img])
    response.resolve()
    return response.text.lower()

def mail_check(text):
#this method is used to check the mail and extract the content that the user wants to send
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
#this method is used to convert the text to speech
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return

def display():
#used to display the conversation between user and bot
  for message in st.session_state["chat_history"]:
    if message["is_user"]:
      dim_text =f"<span style='background-color: yellow;'>You: \n{message['user']}</span>"
      st.write(dim_text, unsafe_allow_html=True)
    else:
      st.write(f"Bot:\n{message['bot']}")
  return

def display_recent():
#used to display the recent conversation between user and bot in case we are seeing the previous chats
  for message in st.session_state["recent_history"]:
    if message["is_user"]:
      dim_text =f"<span style='background-color: yellow;'>You: \n{message['user']}</span>"
      st.write(dim_text, unsafe_allow_html=True)
    else:
      st.write(f"Bot:\n{message['bot']}")
  return


#main method
def main():
#setting the initial values to the session state
  if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
  if "voice_history" not in st.session_state:
    st.session_state["voice_history"] = []
  if "recent_history" not in st.session_state:
    st.session_state["recent_history"] = []
  if "login" not in st.session_state:
    st.session_state.login = False
  
  with st.sidebar:
    selected=option_menu("Bot",["login","chatbot","voicebot"])
   
    
  #this is an interface for chatbot
  #check condition for chatbot and to check the login
  if selected=="chatbot" and "login" in st.session_state and st.session_state.login==True:
    #loading the chat dates from the database
    sql="select date from data where email=%s group by date"
    val=(st.session_state.email,)
    cursor.execute(sql,val)
    result=cursor.fetchall()
    dates=["previous"]
    
    for i in result:
      dates.append(str(i['date']))
    #Displaying the dates on the sidebar as a selectbox
    chatbot_options = st.sidebar.selectbox("Previous Chats", dates)
    #Displaying the user name if the user is logged in
    if "user_name" in st.session_state:
          st.sidebar.write("Welcome",st.session_state.user_name)
    
    st.title("Chat with ChatBOT")
    #Taking the input from the user
    text_input = st.text_input("Type your message here...")
    uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=False)
    search=st.button("click me")
    
    if chatbot_options != "previous":
      #used to display the recent chat history when we are seeing the previous chats
      sql="select * from data where email=%s and date=%s"
      val=(st.session_state.email,chatbot_options)
      cursor.execute(sql,val)
      result=cursor.fetchall()
      recent_chat=""
      st.session_state["recent_history"]=[]
      #storing the recent chat history in the session state for further usage
      
      for i in result:
          recent_chat=recent_chat+i['question']+'\n'+i['response']
          if i['question']!=None:
            st.session_state["recent_history"].insert(0,{"user": i['question'], "is_user": True})
          if i['response']!=None:
            st.session_state["recent_history"].insert(1,{"bot": i['response'], "is_user": False})
          
      if not text_input:
        display_recent()
    #checking if the search button is clicked
    if search:
      mail,content=mail_check(text_input)
      st.session_state["mail"]=mail
      #checking if the mail is present in the text and extracting the content that the user wants to send
      if mail:
        if content:
          with st.spinner("sending..."):
            #sending the mail
              send_mail(mail[0],content)
          st.success("mail sent successfully")
        else:
          st.error("unable to send the mail")
      
      else:
        #if there is no mail context in the text then we are processing the text
        if chatbot_options!="previous":
          #in case we are using previous chats we are taking the recent chat history
          st.session_state["recent_history"].insert(0,{"user": text_input, "is_user": True})
        else:
          #in case we are not using previous chats we are taking the chat history
          st.session_state["chat_history"].insert(0,{"user": text_input, "is_user": True})
        if uploaded_file is not None:
          #checking the file extension and processing the file
          file_extension = uploaded_file.name.split(".")[-1].lower()
          
          if file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg"]:
            #processing the image
            with st.spinner("processing..."):
              response = process_image(uploaded_file,text_input)
              
          elif file_extension=="pdf":
            #processing the pdf
            text=read_pdf(uploaded_file)
            #checking if the text is present in the pdf and processing the text
            if text:
              total_text=text_input+"\nthe below text is the text that was extracted from pdf\n"+text
              with st.spinner("processing..."):
                response = process_text(total_text)
            else:
              response="file is empty or error in reading the file"
              
          elif file_extension=="docx":
            #processing the document
            text=read_docx(uploaded_file)
            #checking if the text is present in the document and processing the text
            if text:
              total_text=text_input+"\nthe below text is the text that was extracted from document\n"+text
              with st.spinner("processing..."):
                response = process_text(total_text)
            else:
              response="file is empty or error in reading the file"
              
          elif file_extension=="txt":
            #processing the text file
            text=read_txt(uploaded_file)
            #checking if the text is present in the text file and processing the text
            if text:
              total_text=text_input+"\nthe below is the text extracted from text file\n"+text
              with st.spinner("processing..."):
                response = process_text(total_text)
            else:
              response="file is empty or error in reading the file"
              
          elif file_extension=="csv":
            #processing the csv file
            text=read_csv(uploaded_file)
            #checking if the text is present in the csv file and processing the text
            if text:
              total_text=text_input+"\nthe below the text that extracted from excel file it was changed as a string\n"+text
              with st.spinner("processing..."):
                response = process_text(total_text)
            else:
              response="file is empty or error in reading the file"
              
          elif file_extension=="wav":
            #processing the audio file
            text=audio_to_text(uploaded_file)
            #checking if the text is present in the audio file and processing the text
            if text:
              total_text=text_input+"\nthe below the text that extracted from audio file\n"+text
              with st.spinner("processing..."):
                response = process_text(total_text)
            else:
              response="file is empty or error in reading the file"
              
          else:
            #if the file is not of the type image or pdf or docx or txt or csv or audio
            response = "uploaded file non type of image or pdf or docx or txt or csv or audio"
            
        else:
          #in case if there were no files uploaded then we process only the text 
          text=text_input
          if chatbot_options!="previous":
            #incase if we are chatiing with the previous chats we are taking the recent chat history
            text=recent_chat+'\nby taking the analysis of above chats answer the below question if needed\n'+text_input
          with st.spinner("processing..."):
            response = process_text(text)
            
          if chatbot_options!="previous":
            #incase if we are chating with the previous chats we are taking the recent chat history
            st.session_state["recent_history"].insert(1,{"bot": response, "is_user": False})
            display_recent()
            
        if chatbot_options!="previous":
          #we make the entry of the chat history into the database if we are using the previous chats to their particular date
          mail=st.session_state.email
          sql="insert into data values(%s,%s,%s,%s)"
          val = (mail,text_input,response,chatbot_options)
          cursor.execute(sql, val)
          conn.commit()  
        else:
          #we make the entry of the chat history into the database to our current date
          mail=st.session_state.email
          date=datetime.datetime.now()
          sql="insert into data values(%s,%s,%s,%s)"
          val = (mail,text_input,response,date)
          cursor.execute(sql, val)
          conn.commit()  
          st.session_state["chat_history"].insert(1,{"bot": response, "is_user": False})
          display()
          
#this is an interface for voicebot   
#checking the login condition and the selected option is voicebot to start the voicebot     
  elif selected=="voicebot"  and "login" in st.session_state and st.session_state.login==True:
    st.empty()
    st.sidebar.empty()
    st.title("Talk with VoiceBOT")
    st.success("Speak Now...")
    #setting the microphone to the source
    with sr.Microphone() as source:
        r = sr.Recognizer()
        r.adjust_for_ambient_noise(source)
#we automate the voice detection and the response to the user when the voice is detected it will be converted to text and then the text will be processed and the response will be given to the user
    while True:
        with sr.Microphone() as source:
            try:
              #listening to the user voice
                audio = r.listen(source)
              #recognizing the user voice using google speech recognition
                text = r.recognize_google(audio, language="en-IN")
                if text:
                #checking if there was extracted any text from the user voice
                  with st.spinner("processing"):
                    response = process_text(text)
                  response=response.replace("*","")
                  mail=st.session_state.email
                  date=datetime.datetime.now()
                #making the entry of the chat into the database
                  sql="insert into data values(%s,%s,%s,%s)"
                  val = (mail,text,response,date)
                  cursor.execute(sql, val)
                  conn.commit() 
                #displaying the user and bot conversation 
                  dim_text =f"<span style='background-color: yellow;'>You: \n{text}</span>"
                  st.write(dim_text, unsafe_allow_html=True)
                  st.write(f"Bot:\n{response}")
                #converting the text to speech and making the bot to speak the response
                  text_to_speech(response)
                  text=""
                print("You said: {}".format(text))
            except Exception as e:
              #if there was any error in the voice detection we ignore and continue the process to detect the voice
                pass
              
              
#this is an interface for login and signup page
  elif selected=="login":
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
    select=st.selectbox("Login/Signup",options=("Login","Signup"))
    
    if select=="Login":
      #if login is selected then we are displaying the login page
        st.subheader("Login Section")
      #taking the input from the user
        mail = st.text_input("Email")
        password = st.text_input("Password",type='password')
        if st.button("Login"):
                sql = "SELECT * FROM register WHERE email = %s and password=%s"
                condition_value = (mail,password)
                # Execute the SQL query with the provided condition
                cursor.execute(sql, condition_value)
                # Fetch the result (in this case, a single integer representing the count)
                result = cursor.fetchall()
                # If the result is not empty, the user exists
                if len(result)==1:
                    for i in result:
                        name1=i['name']
                    st.session_state.user_name=name1
                    st.session_state.login=True
                    st.session_state.email=mail
                    st.balloons()
                    st.success("login successfull")
                else:
                # If the result is empty, the user does not exist
                  st.warning("Invalid Credentials")
                  
        if "user_name" in st.session_state:
          #if the user is logged in then we are displaying the user name on the sidebar and logout button to logout
          st.sidebar.write("Welcome",st.session_state.user_name)
          logout=st.sidebar.button("logout")
          if logout:
            #if the user wants to logout then we are removing the session state values
            st.session_state.pop("login")
            st.session_state.pop("user_name")
            
    if select=="Signup":
      #if the user selects the signup then we are displaying the signup page
        st.subheader("Create New Account")
      #taking the input from the user
        new_user = st.text_input("Name")
        new_password = st.text_input("Strong_Password",type='password')
        new_email = st.text_input("Email")
        new_phone=st.text_input("Phone",max_chars=10)
      #check for email validation
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if st.button("Signup"):
          #if these conditions not were satisfied then we again ask user to fill the details correctly
            if len(new_password)<6 or not re.fullmatch(regex,new_email) or len(new_phone)<10:
                st.error('please fill details correctly')
            else: 
          #else we check if the email is already present in the database or not for the new user
                sql="select * from register where email=%s"
                val=(new_email,)
                cursor.execute(sql,val)
                result=cursor.fetchall()
                if len(result)==1:
                #if the email is already present in the database then we ask the user to login
                    st.warning('Already had an account/please login')
                else:
                #if the email is not present in the database then we are creating a new account for the user
                    sql = "INSERT INTO register VALUES (%s,%s, %s,%s)"
                    val = (new_email,new_password,new_user,new_phone)
                    cursor.execute(sql, val)
                    conn.commit()  
                    st.success("You have successfully created a valid Account")
                    st.info("Go to Login Menu to login") 
                    
 #if the user is not logged in then we are displaying the user to login first
  else:
      st.error("Please login to communicate with bot")    
      
      
      
      
      
      
      
#calling the main method                 
if __name__ == "__main__":
    main()
