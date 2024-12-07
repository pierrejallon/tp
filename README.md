# iese4_sigpro

Ce repository contient le code pour le TD du cours de théorie du signal. 
Pour utiliser le code, vous devez installer les outils suivants:
- git (pour récupérer le code) - https://git-scm.com/downloads
- conda (pour gérer les environnements de développement python) - https://docs.conda.io/en/latest/miniconda.html
Lors de l'installation de conda, il faut ajouter conda au PATH de windows. Par défaut l'option est décochée et un message rouge apparait quand elle est cochée. 
- visual studio code (éditeur de code) - https://code.visualstudio.com/

Une fois les outils installés:
- lancer visual studio code
- dans l'onglet welcome, cliquez sur "Clone git repository"
- Entrez le repo https://github.com/pierrejallon/iese4_sigpro 
- Le logiciel va télécharger le code
- Placez vous dans le dossier iese4_sigpro (visual code le propose quand le code est téléchargé)
- Ajoutez "Python extension for Visual Studio Code" (https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Ouvrir un terminal (menu terminal, new Terminal dans visual studio code)
- Ajouter le repo conda-forge à conda: conda config --add channels conda-forge
- Utiliser la commande: conda create --name td_ts --file requirements.txt
- Activer le nouvel environnement: conda activate td_ts
- Vérifier que le bon interpreteur python est utilisé. Faites Ctrl+Shift+P, sélectionner "Python: select interpreter" et choisissez celui qui correspond à l'environnement td_ts
- Tester l'installation en lancant le script python.exe exe/helloWorld/helloWorld.py

