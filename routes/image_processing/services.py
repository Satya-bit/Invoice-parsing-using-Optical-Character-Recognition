import cv2
import pytesseract
from pytesseract import Output
import pandas as pd
###### Code for image enhancing##########
from PIL import Image
import os


import numpy as np
import sys
import os
from pdf2image import convert_from_path


class ImageEnhancer:
    def convert_pdf_to_image(source_filename,dest_dir,thumbnail_dir):
        """
            Purpose: For given pdf path convert pdf into images and save them
            Input:Path of pdf file and destination path,thumbnail path to store images
            Output: Returns None
        """
        image_lst=convert_from_path(source_filename,1,size=(1654,2340))
        #image_lst=convert_from_path(source_filename,1)

        count=0
        lst_page_path=[]
        for img in image_lst:
            image=np.array(img)
            count+=1
            cv2.imwrite(dest_dir+str(count)+"_page.jpg",image)
            cv2.imwrite(thumbnail_dir+str(count)+"_thumbnail.jpg",cv2.resize(image,(207,293)))
            lst_page_path.append({"index":count,"page_path":dest_dir+str(count)+"_page.jpg","thumbnail_path":thumbnail_dir+str(count)+"_thumbnail.jpg"})
            # print({"pages":lst_page_path})
        return {"pages":lst_page_path}


    #Path of source directory
    # source_dir="../pdf_check_mathscieng/"
    source_dir=os.getcwd()+'/uploads/documents/'
    #source_dir=os.getcwd()+"C:/Users/satya/Documents/uploads/1c0d5221-4a34-438e-a971-e27ca1d11aaa/doc_1c0d5221-4a34-438e-a971-e27ca1d11aaa.pdf"