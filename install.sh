pyinstaller --add-data "./src/*:./src/" --onefile gui.spec
tar -czvf dist ./dist/gui