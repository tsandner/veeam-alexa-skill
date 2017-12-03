# Veeam RESTful API & Amazon Alexa

### Disclaimer
* This project is a private one and not supported by Veeam
* I don't have any programming skills. Everthing was put together using copy & paste and trial and error.
* This is just a demo, but it can easily be extended with more features.

### Purpose
I like Alexa and since I am working at Veeam I thought why not use our RESTful API to use with Alexa :)

This is only a demo how to consume the Veeam RESTful API with Amazon Alexa.

### Demo
[Demo on Youtube](https://www.youtube.com)
### Overview
![2017-11-29 23_42_25-powerpoint-bildschirmprasentation - grafiken pptx](https://user-images.githubusercontent.com/34011056/33403030-05720f88-d55f-11e7-9f3b-d4d0163d0f69.png)

### Local Setup

 1. [Download](https://ngrok.com/download) **ngrok**
 2. Launch **ngrok** on a machine that has access to **Veeam Backup Enterprise Manager Port 9398**
    ```
    ngrok http 5000
    ```
This will expose localhost:5000 to the public internet.
3. [Download](https://www.python.org/downloads/) and install latest version of **Python 3.x**
4. Use pip to install required python modules:
   ```
   pip install requests flask flask_ask unidecode
   ```
5. Download **veeam-alexa-demo.py** and **veeam-alexa.config** to the machine that runs ngrok
6. Edit veeam-alexa.config with your Veeam Backup Enterprise Manager details:
   ```
   server = "enterprisemanager.dns"
   port = 9398
   verifyssl = False
   admin = "hostname\\Administrator"
   password = "verysecurepassword"
   ```
 7. Start the Python flask app
    ```
    python veeam-alexa.py
    ```

### AWS Alexa Setup

1. Goto https://developer.amazon.com/edw/home.html and sign in / create a new developer account
   ![2017-11-26 02_37_06-amazon developer sign in](https://user-images.githubusercontent.com/34011056/33530521-3186f064-d881-11e7-8b35-8e8f1b395df5.png)
   
2. Select **Alexa Skills Kit** and hit **Get started**
   ![2017-11-26 02_37_56-amazon apps services developer portal](https://user-images.githubusercontent.com/34011056/33530557-781c6b44-d881-11e7-8cdb-bc9e4b5a826c.png)
   
3. Hit **Add a New Skill**
    ![2017-11-26 02_38_14-amazon apps services developer portal](https://user-images.githubusercontent.com/34011056/33530527-3d0b8878-d881-11e7-8f6c-0ad464692003.png)
    
4. Skill information:
   Skill Type:  Custom Interaction Model
   * Language: English (U.S.)
   * Name: choose a name
   * Invocation Name: veam (write it this way if you want to call the skill using "Veeam"; you can select any other invocation name of course)
   * Hit **Save** and then **Next**
  ![2017-11-26 02_39_05-amazon apps services developer portal](https://user-images.githubusercontent.com/34011056/33530528-406f303c-d881-11e7-9f7a-eb0cb61326c5.png)

5. Interaction model: Launch **Skill Builder**
	* Intent Schema - open the **Code Editor** on the left
	* Use veeam-intent-schema-ENGL.json
	* **Save & Build Model**
	
6. Go to **Configuration** (top right menue button)
   * Service Endpoint Type: HTTPS
   * Default: use the ngrok https address (step 2 in Local Setup; example: https://19a1e1ff.ngrok.io)
   * Provide geographical region endpoints?: No
   * Account Linking: No
   * Permissions: leave as is (default)
   * Hit **Next**
7. SSL Certificate
	* Select second option: " My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"
	* Hit **Next**
8. Test - Enter Utterances:
	* Give me an overview
	* How many jobs there are
	* Did my jobs run
	* How much free space is left
	* Give me an overview about my repositories
	* How many jobs are running right now
	* How large was last night's backup

### Use the skill with Alexa

1. Use your browser to navigate to alexa.amazon.de & login
2. Go to Skills (left menue)
3. Go to "Your Skills" (top right)
4. You should see your veeam-alexa-demo skill
5. Try it out!


### Credits
* [John Wheeler](https://developer.amazon.com/de/alexa/champions/john-wheeler) for this awesome tutorial & python module: https://alexatutorial.com
* [Timothy Dewin](https://twitter.com/tdewin) for his demo on how to consume Veeam's Restful API https://github.com/tdewin/veeamrestpython
* [Alan Shreve](https://twitter.com/inconshreveable) for https://ngrok.com/
* https://github.com/jbt/markdown-editor which helped me creating this readme.md :)

### Useful links
* https://helpcenter.veeam.com/docs/backup/rest/
* https://forums.veeam.com/restful-api-f30/
