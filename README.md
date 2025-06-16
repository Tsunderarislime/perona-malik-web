# perona-malik-web
This is a simple web application to try out my [Perona-Malik edge enhancement](https://github.com/Tsunderarislime/perona-malik-edge-enhancement) Python code. It uses Flask and Celery as a web backend. It also uses Bootstrap to implement a nicer frontend for users.

---

### Features
- **Fully containerized**: The Docker image will create its own Redis server for the Celery backend, then run all of the necessary processes to operate the web application. Just run the Docker image with `docker compose up` and access the web application at `localhost:8000`.
- **Parallelized Image Processing**: The application assigns each colour channel to a Celery worker to run the Perona-Malik algorithm in parallel. This is effectively the same as the original script I wrote, which used the *multiprocessing* library to run the algorithm in parallel.
- **Automatic Storage Cleanup**: The application will automatically remove images 15 minutes after they have been uploaded. This cleanup also applies to the processed images.
- **Image Name Conflict Resolution**: The application will rename the uploaded image with the hash of the image contents. This addresses an edge case where a user could overwrite another user's image by uploading an image with the same filename.
- **Responsive Web Design**: The application uses Bootstrap to ensure the website is functional on both desktop and mobile web browsers.

### Special Thanks
- **Miguel Grinberg**: They wrote an [incredible guide for writing Flask applications](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). This also included a guide for [using Celery with Flask](https://blog.miguelgrinberg.com/post/using-celery-with-flask), which was also incredibly helpful for my web application. 
- **Dimah Snisarenko**: I used their [image slider component](https://github.com/sneas/img-comparison-slider) for the results page. It's a very nice, easy-to-use solution for overlaying images and comparing before/after.