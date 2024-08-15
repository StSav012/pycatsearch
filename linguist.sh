LINGUIST="pyside6-linguist"
find "src/pycatsearch/gui/i18n" -maxdepth 1 -iname "*.ts" -type f -exec "${LINGUIST}" {} \;
