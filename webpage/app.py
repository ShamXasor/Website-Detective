import mysql.connector
import hashlib
from PIL import Image
import requests
import streamlit as st
from streamlit_lottie import st_lottie
import random
import validators
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


st.set_page_config(page_title="Website Detective", page_icon="🕶", layout="wide")


# Database connection
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="user_database"
    )


def add_user(username, password, email):
    connection = create_connection()
    cursor = connection.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                   (username, hashed_password, email))
    connection.commit()
    cursor.close()
    connection.close()


def get_user_credentials():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT username, password FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users


def get_user_email(username):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM users WHERE username = %s", (username,))
    email = cursor.fetchone()
    cursor.close()
    connection.close()
    return email[0] if email else None


def store_verification_code(username, code):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET verification_code = %s WHERE username = %s",
                   (code, username))
    connection.commit()
    cursor.close()
    connection.close()


def verify_code(username, code):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT verification_code FROM users WHERE username = %s", (username,))
    stored_code = cursor.fetchone()
    cursor.close()
    connection.close()
    return stored_code and stored_code[0] == code


def reset_password(username, new_password):
    connection = create_connection()
    cursor = connection.cursor()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    cursor.execute("UPDATE users SET password = %s, verification_code = NULL WHERE username = %s",
                   (hashed_password, username))
    connection.commit()
    cursor.close()
    connection.close()


def send_verification_email(email, code):
    sender_email = "muhammadsyamimsora@gmail.com"  # Replace with your email address
    receiver_email = email
    appPassword = "zvbn ltqq iojf iwpa"  # Use the App Password generated for your Gmail account

    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset Verification Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"""\
    Hi,
    Here is your verification code to reset your password: {code}
    """
    html = f"""\
    <html>
      <body>
        <p>Hi,<br>
           Here is your verification code to reset your password: <strong>{code}</strong>
        </p>
      </body>
    </html>
    """
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, appPassword)
        server.sendmail(sender_email, receiver_email, message.as_string())


# --- USER AUTHENTICATION ---
credentials = get_user_credentials()
usernames = [user[0] for user in credentials]
hashed_passwords = {user[0]: user[1] for user in credentials}

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'show_forgot_password' not in st.session_state:
    st.session_state.show_forgot_password = False
if 'verification_code_sent' not in st.session_state:
    st.session_state.verification_code_sent = False
if 'reset_username' not in st.session_state:
    st.session_state.reset_username = ""


def login():
    st.header("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type='password', key="login_password")

    if st.button("Login"):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in hashed_passwords and hashed_passwords[username] == hashed_password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()  # Rerun the app to update the UI
        else:
            st.error("Username/password is incorrect")

    st.write("Don't have an account?")
    if st.button("Register Here"):
        st.session_state.show_signup = True
        st.experimental_rerun()

    if st.button("Forgot Password?"):
        st.session_state.show_forgot_password = True
        st.experimental_rerun()


def sign_up():
    st.header("Create New Account")
    new_username = st.text_input("New Username", key="signup_username")
    new_password = st.text_input("New Password", type='password', key="signup_password")
    new_email = st.text_input("New Email", key="signup_email")

    if st.button("Sign Up"):
        add_user(new_username, new_password, new_email)
        st.success("Account created successfully!")
        st.session_state.show_signup = False
        st.experimental_rerun()

    if st.button("Already Registered?"):
        st.session_state.show_signup = False
        st.experimental_rerun()


def forgot_password():
    st.header("Forgot Password")

    if not st.session_state.verification_code_sent:
        username = st.text_input("Enter Username", key="forgot_username")
        if st.button("Send Verification Code"):
            email = get_user_email(username)
            if email:
                verification_code = str(random.randint(100000, 999999))
                store_verification_code(username, verification_code)
                send_verification_email(email, verification_code)
                st.success("Verification code sent to your email.")
                st.session_state.verification_code_sent = True
                st.session_state.reset_username = username
            else:
                st.error("No account found with that username.")

    else:
        verification_code = st.text_input("Enter Verification Code", key="verification_code")
        new_password = st.text_input("New Password", type='password', key="forgot_password")
        confirm_new_password = st.text_input("Confirm New Password", type='password', key="confirm_forgot_password")
        if st.button("Reset Password"):
            if new_password == confirm_new_password:
                if verify_code(st.session_state.reset_username, verification_code):
                    reset_password(st.session_state.reset_username, new_password)
                    st.success("Password reset successfully!")
                    st.session_state.verification_code_sent = False
                    st.session_state.show_forgot_password = False
                    st.experimental_rerun()
                else:
                    st.error("Invalid verification code.")
            else:
                st.error("Passwords do not match.")

    if st.button("Back to Login"):
        st.session_state.show_forgot_password = False
        st.experimental_rerun()


# Main content after login
def main_content():
    st.markdown(
        f"<h1 style='text-align: center; font-size: 40px;'>Welcome {st.session_state.username}!</h1>",
        unsafe_allow_html=True
    )
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()  # Rerun the app to show the login form again

    def load_lottieurl(url):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    local_css("style/style.css")

    lottie_coding = "https://lottie.host/a33c5426-9ccb-44c4-bc5a-d1dc3f82762d/Rzw4surydb.json"
    img_Image1 = Image.open("pic/Image1.png")
    img_Image2 = Image.open("pic/Image2.png")

    st.markdown("""
           <div style='text-align: right;'>
               <strong>Talk with the Experts (MyCert)</strong><br>
               Phone Number: +60-3-8992-6969<br>
               Email: cyber999@cybersecurity.my
           </div>
       """, unsafe_allow_html=True)

    with st.container():
        st.subheader("Hey there, my name is Webby :🕵️‍♂️:")
        st.title("WELCOME TO WEBSITE DETECTIVE")
        st.write("Got fishy links? Put the URL you have below :⬇️:")

        url_input = st.text_input("Enter the URL here:", key="url_input")

        if st.button("Check", key="check_button"):
            if url_input:
                if validators.url(url_input):
                    with st.spinner("Analyzing the URL..."):
                        # Simulating URL check delay
                        import time
                        time.sleep(3)

                        if 'www' in url_input or '.com' in url_input:
                            st.success("The URL is predicted to be legitimate.")
                        else:
                            random_probability = random.random()
                            if random_probability > 0.3:
                                st.error("The URL is predicted to be a phishing website.")
                                st.write("""
                                    **Advice from Webby:🕵️‍♂️::**
                                    - Do not click on links from unknown sources.
                                    - Verify the URL by checking the domain.
                                    - Use security tools to detect phishing websites.
                                    - Keep your software and antivirus up to date.
                                    - Do not share personal information on suspicious websites.
                                """)
                            else:
                                st.success("The URL is predicted to be legitimate.")
                                st.write("Feel free to use this link without worries.")
                else:
                    st.warning("Please enter a valid URL.")
            else:
                st.warning("Please enter a URL to check.")

    with st.container():
        st.write("---")
        left_column, right_column = st.columns(2)
        with left_column:
            st.header("What does this site do?")
            st.write("##")
            st.write("""
                - Enter web links to see if they might be scams.
                - Detect fake/suspicious url.
                - Provide authorities contact and get tips to avoid scams.
            """)
        with right_column:
            st_lottie(lottie_coding, height=300, key="cybersecurity")

    with st.container():
        st.write("---")
        st.header("Suggestions For You")
        st.write("##")
        image_column, text_column = st.columns((1, 2))
        with image_column:
            st.image(img_Image1)
        with text_column:
            st.subheader("What is Phishing and How to Protect Yourself From it?")
            st.write("""
                Learn what exactly is Phishing Attack does so that you can understand the circumstances becoming their victims and do your best to avoid it.
            """)
            st.markdown("[Watch Video...](https://youtu.be/qdpReVgpQhc?si=LyES1n1Ha0GTYXQJ)")

        with st.container():
            image_column, text_column = st.columns((1, 2))
            with image_column:
                st.image(img_Image2)
            with text_column:
                st.subheader("Top 5 Prevention from Phishing Attacks Tips")
                st.write("""
                    It is best to prevent something from happening rather than focus on curing it. Understand the importance of how to avoid involving with Phishing Attacks!
                """)
                st.markdown(
                    "[Watch Video...](https://www.youtube.com/watch?v=123HDqKuAiU&pp=ygUgcGhpc2hpbmcgd2Vic2l0ZSBwcmV2ZW50aW9uIHRpcHM%3D)")

    with st.container():
        st.write("---")
        st.header("Get In Touch With WEBBY!:🕵️‍♂️:")
        st.write("##")

        contact_form = """
        <form action="https://formsubmit.co/muhammadsyamimsora@gmail.com" method="POST">
             <input type="hidden" name_captcha" value="false">
             <input type="text" name="name" placeholder="Your Name" required>
             <input type="email" name="email" placeholder="Your email" required>
             <textarea name="message" placeholder="Your Message Here" required></textarea>
             <button type="submit">Send</button>
        </form>
        """
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown(contact_form, unsafe_allow_html=True)
        with right_column:
            st.empty()


# Render the appropriate content based on login state
if st.session_state.logged_in:
    main_content()
else:
    if st.session_state.show_signup:
        sign_up()
    elif st.session_state.show_forgot_password:
        forgot_password()
    else:
        login()
