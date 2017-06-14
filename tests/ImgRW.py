############
#
# Standard functions to read and write tif files to arrays
#
# Vasco Tenner 2012
###########
from PIL import Image
import numpy as np


def read_tif_image(fname):
    """read image with filename as np array"""
    img = Image.open(fname)
    # positive values correspond to counterclockwise rotation
    img_r = img.rotate(0)
    width = img_r.size[0]
    height = img_r.size[1]
    return np.array(img_r.getdata()).reshape(height,width)


def read_png_image(fname, angle=0):
    """read image with filename as np array"""
    img = Image.open(fname)
    # positive values correspond to counterclockwise rotation
    img_r = img.rotate(angle)
    width = img_r.size[0]
    height = img_r.size[1]
    
    print repr(np.array(img_r.getdata()))
    
    return np.array(img_r.getdata())[:,0].reshape(height,width)



def read_image_fast(fname,skip_errors=False):
    """read tif with filename as np array"""
    data = np.fromfile(fname,np.uint8)
    # endian
    if np.all(data[0:2] == [73,73]):
        le = True
    else:
        le = False
        data.dtype = '>i8'
        raise FileError('Big endian files not supported')

    def readbytes(data,idf_type=3):
        if idf_type == 1:
            return data[0]
        elif idf_type == 2:
            return data[0]
        elif idf_type == 3:
            return data[0]+(data[1]<<8)
        elif idf_type == 4:
            return data[0]+(data[1]<<8)+(data[2]<<16)+(data[3]<<24)
        else:
            error_msg= 'IDF datatype %d not supported'%idf_type
            if skip_errors:
                print error_msg,', but continueing'
            else:
                raise FileError(error_msg)

    def readidf(idfrec):
        """ Return 1 idf record """
        idf_id = readbytes(idfrec[0:2])
        idf_type = readbytes(idfrec[2:4])
        if readbytes(idfrec[4:8],3) > 1:
            error_msg= 'Multiple Counts in 1 IDF not supported'
            if skip_errors:
                print error_msg,', but continueing'
            else:
                raise FileError(error_msg)
        idf_value = readbytes(idfrec[8:12],idf_type)
        return (idf_id,idf_value)

    #read dir offset
    dir_offset = readbytes(data[4:8],3)
    #read number of ifd
    num_ifd = readbytes(data[dir_offset:dir_offset+2])

    #loop through ifds
    bits = None
    dtypew = 'u'
    for i in xrange(num_ifd):
        s=dir_offset+2+12*i
        (idf_id,idf_value) = readidf(data[s:s+12])
        if idf_id == 256:
            width = idf_value
        elif idf_id == 257:
            height = idf_value
        elif idf_id == 258:
            bits = idf_value
        elif idf_id == 259:
            if not (idf_value == 1):
                error_msg= ('Compression %i not supported in file %s'%
                            (idf_value,fname))
                if skip_errors:
                    print error_msg,', but continueing'
                else:
                    raise FileError(error_msg)
        elif idf_id == 262:
            photometic = idf_value
        elif idf_id == 273:
            offset = idf_value #dir_offset+1+num_ifd*6+2
        elif idf_id == 339:
            if idf_value == 1:
                dtypew = 'u'
            elif idf_value== 2:
                dtypew = 'i'
            elif idf_value== 3:
                dtypew = 'f'
            elif idf_value== 6:
                dtypew = 'c'
            else:
                raise FileError('SampleFormat %i not supported in file %s'%(idf_value,fname))

    if np.log(8)/np.log(2)%1 == 0:
        dtype = np.dtype('%s%i' % (dtypew, bits/8))
        data2 = data[offset:]
        data2.dtype = dtype
        return data2.reshape(height,width)
    else:
        raise FileError('Bitdepth %i not supported in file %s'%(bits,fname))
        

def write_16bit_image(imgarray,filename = 'test.tif',showfile=True):
    """
    Write a 16-bit image to file. Automatically detects image size and
    rescales the values into 16-bit integers, with the brightest pixel in the
    image set to normalizeto=65534
    """
    write_img(imgarray,filename,showfile)

def write_16bit_image_scaled(imgarray,filename = 'test.tif',**keywords):
    """
    Write a 16-bit image to file. Automatically detects image size. Scales image
    to (width,height) px and centres image on original canvas
    """
    (height,width) = imgarray.shape
    final_img_16bit = np.array(abs(imgarray), np.uint16)
    out_img = Image.frombuffer("I;16", (width, height), 
                               final_img_16bit, "raw", "I;16",0,1)
    if 'size' in keywords:
        img2 = Image.new("I;16",(width, height))
        img2.paste(out_img(keywords['size'],
                           ((width-keywords['size'][0])/2,
                           (height-keywords['size'][1])/2)))
        img2.save(filename)
    else:
        out_img.save(filename)
    print "Image written with dimensions %i,%i to: %s" % (width,height,filename)


def write_img(data,fname,normalize=-1,showname=True,
        isuint16=False,isabs=False,dtype=np.uint16):
    """ Write abs data to 16bit tiff file. Normalization is possible

    Normalize=-2: normalize to dtype
    Normalize=-1: normalize only if max(data) > 2**16
    Normalize=0: do not normalize, wrap from 2**16 to 0
    Normalize=number: normalize with number as maximum value

    showname toggle output of filename
    
    isuint16 OBSOLETE
    isabs = True  does not take absolute value

    dtype = type of output file, supported: 
             np.uint8, np.uint16, np.int32 (max 2**30),
             np.float32, np.complex128
    """
    # ImageJ is strange
    dtype = np.dtype(dtype)
    bytesperitem = np.dtype(dtype).itemsize
    if dtype == np.uint8 or dtype == np.uint16:
        kind = 1
        maxvalue = 2**(bytesperitem*8)-1
    elif dtype == np.int32:
        kind = 2
        maxvalue = 2**(31)-1
    elif dtype == np.uint32:
        print 'ImageJ compatibility mode, max = 2**30-1'
        kind = 1
        maxvalue = 2**(30)-1
    elif dtype == np.int8 or dtype == np.int16:
        print 'Type %s not supported by ImageJ' % dtype
        kind = 2
        maxvalue = 2**(bytesperitem*8-1)-1
    elif dtype == np.float32:
        kind = 3
        maxvalue = 1.
        if normalize == -1 or normalize == -2 or normalize == 'max':
            normalize = 0
    elif dtype == np.complex128:
        kind = 6
        if normalize == -1 or normalize == -2 or normalize == 'max':
            normalize = 0
    else:
        print 'Type %s not supported' % dtype
        return None

    #some functions to write 64bit bytes from 8bit bytes
    def cba4(number):
        """show number as TIF bytes"""
        a = number>>8*3
        b = (number>>8*2)-(a<<8)
        c = (number>>8*1)-(b<<8)-(a<<8*2)
        d = number-(c<<8)-(b<<8*2)-(a<<8*3)
        return [d,c,b,a]

    def cba2(number):
        """show number as TIF bytes"""
        c = number>>8*1
        d = number-(c<<8)
        return [d,c]
    # make header
    numberifd = 9
    header=np.zeros(10+numberifd*12+4,dtype=np.uint8)
    header[0:8] = [73,73,42,0,8,0,0,0]
    # set number of IFDs
    header[8:10] = [numberifd,0]
    s=10
    header[s:s+2]=cba2(256) # first IDF (width ,256)
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(data.shape[1]) # value
    s=10+12*1
    header[s:s+2]=cba2(257) # second IDF (height ,257)
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(data.shape[0]) # value
    s=10+12*2
    header[s:s+2]=cba2(258) # bits per sample 258
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(bytesperitem * 8) # value
    s=10+12*3
    header[s:s+2]=cba2(259) # compression
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(1) # value
    s=10+12*4
    header[s:s+2]=cba2(262) # photometric
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(1) # value
    s=10+12*5
    header[s:s+2]=cba2(273) # StripOffsets
    header[s+2:s+4]=cba2(4) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(10+numberifd*12+4) # value
    s=10+12*6
    header[s:s+2]=cba2(278) # RowsPerStrip
    header[s+2:s+4]=cba2(4) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(data.shape[0]) # value
    s=10+12*7
    header[s:s+2]=cba2(279) # StripByteCounts
    header[s+2:s+4]=cba2(4) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(data.size*bytesperitem) # value
    s=10+12*8
    header[s:s+2]=cba2(339) # SampleFormat
    header[s+2:s+4]=cba2(3) #type
    header[s+4:s+8]=cba4(1) # number of values
    header[s+8:s+12]=cba4(kind) # value

    f=open(fname,'wb')
    f.write(header)
    if (not isabs) and kind == 1:
        data_abs = abs(data)
    else:
        data_abs = data
    if normalize == -1:
        if kind == 2:
            data_max = np.max(data_abs)
        else:
            data_max = np.max(np.abs(data_abs))
        if data_max >= 2**(bytesperitem * 8):
            f.write((data_abs/(1.*data_max)*maxvalue).astype(dtype))
        else:
            f.write(data_abs.astype(dtype))
    elif normalize == 0:
        f.write(data_abs.astype(dtype))
    elif normalize == 'max' or normalize == -2:
        if kind == 2:
            data_max = np.max(data_abs)
        else:
            data_max = np.max(np.abs(data_abs))
        f.write((data_abs/(1.*data_max)*maxvalue).astype(dtype))
    else:
        f.write((data_abs*normalize).astype(dtype))
    f.close()
    if showname:
        print "Image written with dtype %s and dimensions %i,%i to: %s" % (
                dtype,
                data.shape[1],
                data.shape[0],fname)

class FileError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
         
