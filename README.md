# perona-malik-web
This is a simple web application to try out my [Perona-Malik edge enhancement](https://github.com/Tsunderarislime/perona-malik-edge-enhancement) Python code. It uses Flask, Celery, and Redis as a web backend. It also uses Bootstrap to implement a nicer frontend for users.

---

### Features
- **Fully containerized**: The Docker image will create its own Redis server for the Celery backend, then run all of the necessary processes to operate the web application. Just run the Docker image with `docker compose up` and access the web application at `localhost:8000`.
- **Parallelized Image Processing**: The application assigns each colour channel to a Celery worker to run the Perona-Malik algorithm in parallel. This is effectively the same as the original script I wrote, which used the *multiprocessing* library to run the algorithm in parallel.
- **Automatic Storage Cleanup**: The application will automatically remove images 15 minutes after they have been uploaded. This cleanup also applies to the processed images.
- **Image Name Conflict Resolution**: The application will rename the uploaded image with the hash of the image contents. This addresses an edge case where a user could overwrite another user's image by uploading an image with the same filename.
- **Responsive Web Design**: The application uses Bootstrap to ensure the website is functional on both desktop and mobile web browsers.
<p align="center">
  <b>Landscape View</b> <br>
  <img src="https://github.com/user-attachments/assets/145528a9-b48c-482e-82f8-8fdeb716618d" style="width: 85%;"/> <br> <br>
  <b>Portrait View</b> <br>
  <img src="https://github.com/user-attachments/assets/4d8889c7-b227-417c-a607-0921d0ad4f87" style="width: 55%;"/>
</p>

- **Image Comparison Slider**: The application will display the image before and after running the Perona-Malik algorithm. You can move a slider back and forth to see the difference. You can also save the processed image to your device.
<p align="center">
  <img src="https://github.com/user-attachments/assets/f6d49ef6-abcc-4058-a498-e7ffda79b1a3" style="width: 85%;"/>
</p>

### How to Use
**I **strongly recommend** just using Docker and building the Docker image**. However, if you DO want to try running my web application without Docker, you still can.
#### Docker
1. Clone this repository anywhere on your computer.
2. Ensure your Docker engine is running.
3. Run `docker compose up`.
4. Go to `localhost:8000` to see the web application.
5. Use **Ctrl+C** to stop the web application.

#### No Docker
1. Make sure [Python](https://www.python.org/) and [Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/) are installed.
2. Clone this repository anywhere on your computer.
3. Install the required Python modules with `pip install -r requirements.txt`
4. Run the Redis server with `redis-server` in one terminal.
5. Run the Celery worker with `celery -A app.celery worker loglevel=INFO` in another terminal.
6. Run the Celery beat with `celery -A app.celery beat --loglevel=INFO` in yet another terminal.
7. Run the web application with `gunicorn --bind 0.0.0.0:8000 app:app` in one more terminal.
8. Go to `localhost:8000` to see the web application.
9. Use **Ctrl+C** on each terminal window to stop the web application.

While you can run these all in the background and avoid having 4 terminal windows open, it's a lot easier to exit the processes if you run these in their own terminal windows.

### Special Thanks
- [Miguel Grinberg](https://github.com/miguelgrinberg): They wrote an [incredible guide for writing Flask applications](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). This also included a guide for [using Celery with Flask](https://blog.miguelgrinberg.com/post/using-celery-with-flask), which was also incredibly helpful for my web application. 
- [Dimah Snisarenko](https://github.com/sneas): I used their [image slider component](https://github.com/sneas/img-comparison-slider) for the results page. It's a very nice, easy-to-use solution for overlaying images and comparing before/after.
- [ほったりょう](https://x.com/hottaryou): I like their illustrations, so I used one of them to showcase an example of how my web application works. Give them a follow on X (formerly known as Twitter).
