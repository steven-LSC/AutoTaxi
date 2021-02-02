# AutoTaxi

![image](https://github.com/steven-LSC/AutoTaxi/blob/main/Logo.png)

This is an AI automated taxi system that we hope can be merged with self-driving cars. There are two modes in total: patrol model and order mode.

* Line Chatbot: We use Line to build user interface, including: uploading selfies, account management, and interactive messages.

* Patrol mode: While the self-drving car is patroling, it will detect the member who is hailing, and then confirm the intention through Line chatbot.

* Order mode : After getting the order from a member, the car will departure and find the member. 

We control the Raspberry Pi car to simulate the self-driving car, and then build the entire system through a camera, AWS, and AI models.


### Demo Video
https://youtu.be/ZHJN7UXx9a0

### Operation Logic

#### Patrol Mode
![image](https://github.com/steven-LSC/AutoTaxi/blob/main/patrol%20mode%20diagram.png)

#### Order Mode
![image](https://github.com/steven-LSC/AutoTaxi/blob/main/oreder%20mode%20diagram.png)

#### Member Management
![image](https://github.com/steven-LSC/AutoTaxi/blob/main/member%20management%20diagram.png)

### Tech
* Respberry Pi
* Line Chatbot
* OpenPose
* AWS S3
* AWS Rekognition
* Deep Learning Model for face comparison
* Object Detection model
