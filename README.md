# Invoice-parsing-using-Optical-Character-Recognition
User can upload the invoice and the data can be fetched automatically

# OVERVIEW

Inefficient manual processing of invoices and purchase orders can lead to errors, delays, and increased costs for businesses. To address this issue, I have developed a user interface that allows users to upload four different templates of invoices , and automatically fetches the relevant details to display on the UI. However, I recognize that there may still be challenges related to ensuring the accuracy and completeness of the data. My goal is to identify and address these issues in order to provide a more streamlined and efficient process for businesses to manage their invoices and purchase orders.

# PROJECT OVERVIEW

The project intends to deliver a user-friendly invoice upload interface and a secure login authentication system with password reset capability. The system will automatically extract the pertinent information from four different invoice templates and show it on the user interface. The data can be edited and deleted by users as necessary.

Authentication System: The login authentication system will provide a secure way for users to access the system with their unique login credentials. Password reset functionality will also be available in case users forget their password.

User Interface: Users will be able to upload invoices quickly and easily in one of the four pre-defined templates. The relevant information will be retrieved and presented on the interface for simple viewing.

Invoice Templates: The system will support four different invoice templates, each with a specific format for the invoice data. The system will be able to extract data from each template automatically, and display it in a clear and organized manner on the interface.

Data Editing and Deletion: Users can edit and delete the data they have uploaded, ensuring that the system is always up to date with accurate information.
In summary, the project will provide a secure, user-friendly interface for managing invoices, with automatic data extraction and editing capabilities.

# SOFTWARE SPECIFICATIONS

The software specifications for this project are focused on the development of a web application using the Python programming language as the primary backend language, the Flask web framework to provide a structured and modular approach to development, and the MongoDB database management system for efficient and scalable data storage and retrieval. The frontend of the web application is developed using a combination of HTML, CSS, and JavaScript to provide a clean and user-friendly interface. The development environment used for the project is Visual Studio Code.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/2112e1ad-2b68-4120-a85b-e3c74484a8fa)

# WORKFLOW

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/e6acee2f-31ff-4c67-b0b1-d8d6b05dcbdf)

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/ee5c4789-3646-42bd-986b-5d3633b548b5)

# TYPE OF INVOICES

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/1f8e54d2-ce11-41fd-89e2-c66e4d6ff413)

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/3dceb87a-2460-418a-986f-22e43b422308)

# LOGIN AUTHENTICATION

->JWT(JSON Web Token) is used for Login system.

->First the user has to create his/her account. Password is stored as hashed value using PKDF2_SHA256(Password Base Key Derivation Function). Whenever the user tries to login and if the email is found in the database and the password matches then the user is able to login.

->For forgot password functionality, a password reset token using UUID(Universally Unique Identifier) is created along with password reset timestamp.

->If the email Id is found in the database then a link is sent for reset password. This is done with the help of SMTP(Simple Mail Transfer Protocol) server of Gmail.

=> SIGNUP PAGE

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/48140cf6-ed52-4f81-9e64-e1b74927fcef)

->This is the signup page where the user has to enter details like name, Email and Password.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/296517e2-60b9-4cfc-bfe1-5355f30cdc1f)

-> In the database the entry would be like below

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/75a59924-0a7b-4531-b7ba-524827224b53)

-> The user can also do FORGOT PASSWORD and reset it

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/70d39e74-0ae2-4d6e-8cf6-a0744f2f9bf9)

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/f3441908-8ddb-4037-b479-553956f9cbcc)

# STEPS TO UPLOAD AND VIEW DATA

-> After the user logins he/she is redirected to dashboard page which looks like below.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/c388c0f6-32e8-487f-8e1c-8738fc737df6)

->He/she has to upload the file and click on the submit button and press view data button which will redirected to the page as shown below.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/e98dd839-c102-47cc-8a25-ca74b98b11f4)

-> The user can also edit and delete the data of the invoice.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/0bc17ac3-7482-401e-b0f7-3ae716db72a7)

-> He/she can also edit and add the items table if needed.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/cc3182f8-c927-41b6-ac97-445edf9aad7b)

-> The user can also view data in excel.

![image](https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/267ce90a-ac13-48c6-ae53-1357df4a8869)

# DEMO OF MY PROJECT

https://github.com/Satya-bit/Invoice-parsing-using-Optical-Character-Recognition/assets/70309925/79c7f6c1-f5c5-4489-a2e6-51f547c5b47a



