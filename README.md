# Storanonymizer
A platform to host story writing contests. Setup a contest, create different rounds, let your writer friends contribute and vote on the best story. Contributions are anonymized in the voting round so everyone can judge the pieces objectively. The platform keeps track of the score of each writer and determines the complete, ongoing story as you progress through different rounds.

## Quickstart
1. Build a Docker image
2. Specify a Docker Volume for the SQLite database
3. Run container
   ```
   docker run -d --rm -p 5000:5000 -v escape-db:/data storanonymizer:3.1
   ````

## Screenshots
A story contribution
![A story contribution](/screenshots/contribution.png)

Overview of a round
![Overview of a round](/screenshots/round.png)
