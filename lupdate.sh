py_files=$(find src/pycatsearch/gui -iname "*.py" -type f)
L_UPDATE="../qt-linguist/lupdate.py"
if [[ -e ${L_UPDATE} ]]; then L_UPDATE="python ${L_UPDATE}"; else L_UPDATE="pyside6-lupdate"; fi
echo using "${L_UPDATE}"
for n in src/pycatsearch/gui/i18n/*.ts; do
  ${L_UPDATE} "${py_files}" -ts "${n}" "$@"
done
