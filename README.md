# Distributed-Computing---Assignment-01
Distributed Word Counting System

## System Start
   Execute these on seperate terminal windows:

   ```bash
   # Coordinator 
   python script.py --role coordinator
   ```

   ```bash
   # Proposer 1 
   python script.py --role proposer --range A-M --port 1002
   ```

   ```bash
   # Proposer 2
   python script.py --role proposer2 --range N-Z --port 1003
   ```

   ```bash
   # Acceptor 1 
   python script.py --role acceptor --port 1004
   ```

   ```bash
   # Acceptor 2 
   python script.py --role acceptor2 --port 1005
   ```

   ```bash
   # Learner (Port 1006)
   python script.py --role learner
   ```
