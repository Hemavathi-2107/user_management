Final Project: User Management System
Project Objective
The User Management System project aimed to develop a secure, feature-rich application for managing user accounts, roles, and permissions. It included functionalities such as user registration, authentication,  and advanced features like minio profile picture upload. The project emphasized modern development practices, integrating CI/CD pipelines, Dockerized deployment, and comprehensive testing. With a focus on scalability and security, the system was designed to meet real-world web application standards while offering a seamless user and administrator experience. The successful deployment to DockerHub highlighted the project's readiness for production.

The submission meets the following goals:
Fixed five QA Issues/Bugs across the code.
Implements a NEW feature-1Profile Picture Upload with Minio into the existing code.
Created 10 NEW Tests for the new feature implemented.
Includes a Reflection Document for the course.

Setup and Preliminary Steps:
1.Fork the Project Repository: Fork the project repository to my own GitHub account.
2.Clone the repository to your local machine: Clone the forked repository to our local machine using the git clone command. This creates a local copy of the repository on our computer, enabling we make changes and run the project locally.
git clone https://github.com/Hemavathi-2107/user_management.git

3.Change directory to the project
cd user_management and open code in  vistual studio write cmd: code .

4.Install and Setup Docker [compulsory]
Verify the Project Setup: Follow the steps in the instructor video to set up the project using Docker. Docker allows our to package the application with all its dependencies into a standardized unit called a container. Verify that you can access the API documentation at http://localhost/docs and the database using PGAdmin at http://localhost:5050.
5.Commands:
docker compose up --build
Running tests using pytest
docker compose exec fastapi pytest
Need to apply database migrationss: docker compose exec fastapi alembic upgrade head
Upload Image to minIO : docker compose exec fastapi python3 -m app.utils.minio_client

Access various components
PgAdmin: http://localhost:5050
FastAPI Swagger UI: http://localhost/docs
MinIO console app open : http://localhost:9001
MinIO API : http://localhost:9000

Issues Fixed
The following issues were resolved:

[1- Fix_dockerfile_allow build_libc-bin_version permit](https://github.com/Hemavathi-2107/user_management/issues/1)
--allow-downgrades: Ensures that the package manager permits downgrading libc-bin to the specified version (2.36-9+deb12u7).
Updated the Docker File to allow build.
Resolved Application Errors: Fixed issues caused by mismatched library versions to ensure smooth application functionality.

[Profile picture URL validation](https://github.com/Hemavathi-2107/user_management/issues/4)
Ensured the provided URL is well-formed and points to an image file by validating that it ends with standard image extensions
such as .jpg, .jpeg or .png.
Implemented robust URL validation mechanisms to ensure secure and valid profile picture uploads. This includes verifying that the URL is properly structured, ends with acceptable image file extensions, and optionally confirming the URL's accessibility and that it references a valid image resource.

[User ID being passed as None in the user verification email has been resolved](https://github.com/Hemavathi-2107/user_management/issues/6)
The problem of the User ID being None in the email verification process has been fixed.
The email is now sent only once, when the user is either created or updated in the database.
The code has been updated to ensure that the correct User ID is passed and displayed in the email verification, eliminating the
issue of None being shown.

[Nickname Assign and Uniqueness in User Registration](https://github.com/Hemavathi-2107/user_management/issues/8)
Removed the call to the generate_nickname() function when assigning a new user's nickname.
Instead, the nickname is now directly set using the provided user data (user_data["nickname"]).
The system checks for uniqueness of the provided nickname in the database.

[Password Validation in User Registration](https://github.com/Hemavathi-2107/user_management/issues/10)
The implementation of password validation logic used during user registration to ensure strong and secure passwords.
Key Features of the Validation:
Minimum Length Requirement: Passwords must be at least 8 characters long.
Uppercase Letter Check: Passwords must include at least one uppercase letter (A-Z).
Lowercase Letter Check: Passwords must include at least one lowercase letter (a-z).
Digit Check: Passwords must include at least one numeric digit (0-9).
Special Character Requirement: Passwords must contain at least one special character from the set !@#$%^&*(),.?":{}|<>.

[Email verification](https://github.com/Hemavathi-2107/user_management/issues/15)
Issue: User roles were downgraded unintentionally during email verification.
Fix: Ensured roles are preserved during the email verification process.

Profile Picture Upload with Minio :
This feature enhances the user profile management system by enabling users to upload and store profile pictures using Minio, a distributed object storage system. By personalizing their accounts with profile pictures, users gain a more engaging and tailored experience. The functionality focuses on secure storage, efficient retrieval, and seamless integration with the existing user profile management system.

Description of Implementation:

1.API Endpoint for Uploading Profile Pictures:
Create a dedicated API endpoint for handling profile picture uploads.
Accept file uploads and validate the image format ( Supported e.g JPEG, PNG, GIF.) and size ( e.g.up to 5MB).
2.Integration with Minio:
Configure Minio to securely store uploaded images in dedicated bucket.
Generate a unique key for each image to avoid overwriting files.
Use Minio REST API to upload images and retrieve their URLs.
3.Update User Profile Management:
Add a new field in the user profile schema to store the profile picture URL.
Update existing APIs to include the profile picture URL in responses.
4.Image Retrieval:
Fetch the profile picture URL from Minio when displaying user profiles.
Use Minio to create presigned URLs for safe and effective retrieval.
Provide a default profile picture for users without an uploaded image.

Final_user_management_output:  


Testing and Validation:
Write Unit tests to verify the upload, storage, and retrieval workflows.
Validate image formats and restrict sizes to ensure consistent uploads.
Write Integration tests:
tested every step of the process, from upload to display.
Verify that API endpoints provide accurate information for both valid and invalid inputs.

Testing & QA
Added 10 test cases: 
Link for 1-4 testcases: [Test Cases Link](https://github.com/Hemavathi-2107/user_management/issues/19)
Link for 5-8 testcases: https://github.com/Hemavathi-2107/user_management/issues/21
Link for 9-10 testcases: https://github.com/Hemavathi-2107/user_management/issues/23

Implemented unit tests to validate:
1.Upload Profile Picture with Bytes
2.Upload Profile Picture with File‑Like Object
3.Upload Profile Picture Unsupported Extension
4.Get Profile Picture URL
5.Successful email send
6.Authentication failure
7.Recipient refused
8.Generic exception on connection
9.Missing template read
10.Email-style inlining on HTML tags

Test Coverage above 91% : ![test coverage](image.png)

Docker Deployment:
![alt text](image-1.png)
![alt text](image-2.png)
Docker Repository: https://hub.docker.com/repository/docker/hemarathinam/user_management/general

Reflection Document:

