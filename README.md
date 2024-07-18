# Owmail - owmail.co
### Video Demo: https://youtu.be/ztL8lEsTKsM
A small web-based email client, created as a temporary personal alternative to platforms like Gmail. Built with Flask, CSS, and HTML. SMTP run by Sendgrid API, with emails stored with sqlite. Temporarily hosted on a Linode with an Nginx WSGI + Gunicorn for python functionality. 

The static files contain styles.css and a favicon that I used for the site. The templates file contains all 8 HTML pages. Signup.html file allows users to create owmail accounts. Full_email.html displays SQL email data in an email format. Inbox.html displays all of your emails in a tabular format. Styles managed by Bootstrap.

App. py is the main program. In total there are 8 routes. Sendgrid uses an API key to send emails, which can be integrated into python to send emails dynamically. The send route allows you to send an email using the API key, fetching the users address, and using requests to check the contents and recipients of the email. A Sendgrid mail object is then compiled and sent. I used Sqlite with python to fetch all email data from a secure database depending on the current logged in user. After testing on a localhost, I set up a Linode connected to namservers from a custom domain (owmail.co), setting up SSH access and Linode config files. I finally used the secure copy protocol (SCP) command to move files over. 
