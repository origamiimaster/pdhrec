# PDHREC: Pauper Commander Card Recommendations
**See the live version of the site [here](https://pdhrec.com)!**


## What is Pauper Commander?
Pauper Commander / Pauper Dragon Highlander is a Magic the Gathering format that is a cross between Pauper and EDH (commander).  

Check out the rules at the [PDH Homebase](https://pdhhomebase.com).  



## What does this website do?
[PDHREC](https://pdhrec.com) is based on the website [EDHREC](https://edhrec.com), a website 
that recommends cards for use in commander decks.  

After collecting deck information from thousands of decks, users can see what the best cards are for any particular deck, or for a particular color.  

## Building the PDHREC-dev environment:
1. Clone the repository with `git clone https://github.com/origamiimaster/pdhrec.git`.  
2. Get a connection string for the MongoDB instance you want to use.  A 
   straightforward method is to create an account with [MongoDB Atlas](https://www.mongodb.com/atlas/database), the 
   free tier will be plenty for running PDHREC.  Create a file in the 
   `pdhrec` folder called `server-token.json` and fill it with ```{"connection": "YOUR CONNECTION STRING HERE"}```
3. Install [eleventy](https://www.11ty.dev/docs/getting-started/), a static 
   site generator.  The build script uses a global install, so run `npm install -g @11ty/eleventy` after making sure you have NodeJS.  
4. Run the `generate_frontend_doc.py` first.  It will take some time as it 
   gathers all of the data from the different sources, and saves it into the 
   database for the first time.  
5. Navigate into the `frontend` folder, and run the shell script `./build.sh`.  On windows, you can empty the build folder and then run `eleventy --formats=html,css,js,liquid,md --output=build`.  
6. Host the static site with your favorite hosting services, for development the simple `python3 -m http.server --directory build` works great.  
7. Open a web browser and navigate to [127.0.0.1:8000](127.0.0.1:8000).  
