SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
echo $SCRIPTPATH
pyinstaller --add-data "./src/*:./src/" --onefile $SCRIPTPATH/gui.spec
tar -czvf $SCRIPTPATH/dist/dist.tar.gz $SCRIPTPATH/dist/gui