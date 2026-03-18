#!/bin/bash
if [[ FILES.txt != "" ]]
then
    cd /advance/work/endf/${SUBLIB}
    echo "The ff. are new or changed files..."
    cat FILES.txt
    
    # The important number '3' in the ff. while loop is the 
    # arbitrarily-assigned file descriptor for the
    # input file 'FILES.txt'.  Without it, inputs will be read
    # from standard input and not from the input file.  
    # RESULT: the filename in the first line of 'FILES.txt' 
    # will be the only one read and processed and the
    # remaining lines in the file seen as part of the first line.
    #
    while read filename <&3; do
        #if [[ $line != ".gitlab-ci.yml" ]] &&  [[ $line != "verify.sh" ]] && [[ $line != "verify2.sh" ]] 
        # Determine the file extension
        if [ "${filename##*.}" == "endf" ]
        then
        #echo "file extension: ${filename##*.}"
        echo " "; echo "......................"
        echo "filename:  ${filename%.*}"
        scons "${filename%.*}"
        #
        # Delete the '*.png, *.xml, *.ps, *.ace, *.boxr' files in the root directory of the material
        # so that they will not be included in the artifacts generation
        #
        cd "${filename%.*}"
        rm  -f *.png *.xml *.ps *.ace *.boxr 
        #cp  -p /advance/advance/base/static/common/templates/markdownTemplates/README.md  .
        cd ..
        rm  -f README.md
        zip -qr "${filename%.*}".zip  "${filename%.*}"/
        mv  /advance/work/endf/${SUBLIB}/"${filename%.*}".zip  ${CI_PROJECT_DIR}
        fi
    done 3< "FILES.txt" 

    # 
    # Move artifacts to the project's build directory
    # so that GitLab can see and download them as one
    # zipped file. 
    # mv  /advance/work/endf/${SUBLIB}/*   ${CI_PROJECT_DIR}
fi
