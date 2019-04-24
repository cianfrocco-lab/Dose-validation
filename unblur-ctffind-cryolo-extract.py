#!/usr/bin/env python
import shutil 
import os
import glob
import linecache 
import subprocess

indir='Movies/14sep05c_c_00004gr_00031sq_000*.mrc'
moviedir='Movies'
gain_ref='Movies/norm-amibox05-0.mrc'
apix=0.66
cs=2.7
kev=300
totframes=38
outdirname='dose201904242'
ctfoutfile1='%s/micrographs_ctf.star' %(outdirname) #output ctf file
boxsize=512
newbox=340
diameter=200 #pixels 
os.makedirs(outdirname)
def unblur(inmovie,startframe,finalframe):

	submitfile='%s_submit.txt' %(inmovie[:-5])
	if os.path.exists(submitfile):
		os.remove(submitfile)

	if os.path.exists('%s_1_%i.mrc' %(inmovie[:-5],finalframe)):
		os.remove('%s_1_%i.mrc' %(inmovie[:-5],finalframe))

	o1=open(submitfile,'w')
	o1.write('''#!/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N unblur
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=1,pmem=12gb
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=72:00:00
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

# Ensure the necessary modules are loaded
module load gcc/4.9.4
module load openmpi/3.1.2/gcc/4.9.4
module load relion/3.0_beta-cluster/openmpi/3.1.2
module load imod 
# Switch to the working directory
cd $PBS_O_WORKDIR
\n''')

	cmd='''/programs/x/cistem/1.0.0-beta/bin/unblur << eof
%s
%s_%i_%i.mrc
0.885
1
no
yes
2
80
1500
1 
1
1
20
no
%s
%i
%i
no
eof\n''' %(inmovie,inmovie[:-5],startframe,finalframe,gain_ref,startframe,finalframe)
	o1.write(cmd)
	o1.close()
	alignedmic='%s_%i_%i.mrc' %(inmovie[:-5],startframe,finalframe)
	cmd='qsub %s' %(submitfile)
        subprocess.Popen(cmd,shell=True).wait()

	return alignedmic

def tif2mrc_unblur_align_ctf(inmovie,startframe,finalframe,kev,cs,apix):

	submitfile='%s_submit.txt' %(inmovie[:-5])
	if os.path.exists(submitfile):
		os.remove(submitfile)

	if os.path.exists('%s.mrc' %(inmovie[:-5])):
		os.remove('%s.mrc' %(inmovie[:-5]))

	if os.path.exists('%s_1_%i.mrc' %(inmovie[:-5],finalframe)):
		os.remove('%s_1_%i.mrc' %(inmovie[:-5],finalframe))

	o1=open(submitfile,'w')
	o1.write('''#!/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N unblur-ctf-dose
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=1,pmem=12gb
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=72:00:00
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

# Ensure the necessary modules are loaded
module load gcc/4.9.4
module load openmpi/3.1.2/gcc/4.9.4
module load relion/3.0_beta-cluster/openmpi/3.1.2
module load imod 
# Switch to the working directory
cd $PBS_O_WORKDIR
tif2mrc %s %s.mrc\n'''%(movie,movie[:-5]))

	cmd='''/programs/x/cistem/1.0.0-beta/bin/unblur << eof
%s
%s_%i_%i.mrc
0.885
1
no
yes
2
80
1500
1 
1
1
20
no
%s
%i
%i
no
eof\n''' %(inmovie,inmovie[:-5],startframe,finalframe,gain_ref,startframe,finalframe)
	o1.write(cmd)
	alignedmic='%s_%i_%i.mrc' %(inmovie[:-5],startframe,finalframe)
	if os.path.exists('%s_diag.txt' %(alignedmic[:-4])):
		os.remove('%s_diag.txt' %(alignedmic[:-4]))
        cmd='''/programs/x/ctffind4/4.1.8/bin/ctffind << eof
%s
%s_diag.mrc
%f
%i
%f
0.07
512
30
5
5000
50000
500
no
no
yes
200
no
no''' %(alignedmic,alignedmic[:-4],apix,kev,cs)
	o1.write(cmd)
	o1.close()
	cmd='qsub %s' %(submitfile)
	subprocess.Popen(cmd,shell=True).wait()

	return '%s_diag.txt' %(alignedmic[:-4])

def extract(outdir,ctf,boxsize,suffix):

	if os.path.exists('%s/dose%s/' %(outdir,suffix)): 
		shutil.rmtree('%s/dose%s/' %(outdir,suffix))
	os.makedirs('%s/dose%s/' %(outdir,suffix))
	submitfile='%s/dose%s/extract.run' %(outdir,suffix)
	o1=open(submitfile,'w')
        o1.write('''#!/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N relion-extract
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=20,pmem=12gb
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=72:00:00
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

# Ensure the necessary modules are loaded
module load gcc/4.9.4
module load openmpi/3.1.2/gcc/4.9.4
module load relion/3.0_beta-cluster/openmpi/3.1.2
module load imod 
# Switch to the working directory
cd $PBS_O_WORKDIR\n''')
	
	cmd='mpirun -np 20 relion_preprocess_mpi --i %s --coord_dir %s/ --coord_suffix .star --part_star %s/dose%s/particles.star --part_dir %s/dose%s/ --extract --extract_size %i --norm --bg_radius %i --white_dust -1 --black_dust -1 --invert_contrast --scale %i  > %s/dose%s/run.out 2> %s/dose%s/run.err < /dev/null' %(ctf,outdir,outdir,suffix,outdir,suffix,boxsize,(newbox/2)*0.8,newbox,outdir,suffix,outdir,suffix)
	o1.write('%s\n' %(cmd))
	#subprocess.Popen(cmd,shell=True).wait()
	o1.close()
	cmd='qsub %s' %(submitfile)
        subprocess.Popen(cmd,shell=True).wait()

waitinglist=[]

for movie in glob.glob(indir): 

	submitmic=tif2mrc_unblur_align_ctf(movie,1,totframes,kev,cs,apix)
	waitinglist.append(submitmic)

#Wait for unblur to finish
isdone=0
while isdone == 0: 
	totalcheck=len(waitinglist)
	counter=0
	finish_check=0
	while counter < totalcheck:
		if os.path.exists(waitinglist[counter]):
			finish_check=finish_check+1
		counter=counter+1

	if finish_check == totalcheck:
		isdone=1

#Submit cryolo
pwd=os.getcwd()
#Symlink mics
for mic in waitinglist: 
	os.symlink('%s/%s.mrc' %(pwd,mic[:-9]),'%s/%s/%s.mrc' %(pwd,outdirname,mic.split('/')[-1][:-9]))

#Submit cryolo: 
cmd='/lsi/groups/cryoem-workshop/shared_software/cryolo/submit_cryolo.py --dir=%s/%s/ --diam=%i --thresh=0.1' %(pwd,outdirname,diameter)
subprocess.Popen(cmd,shell=True).wait()	

#Start waiting to finish
isdone=0
while isdone == 0:
	if os.path.exists('%s/%s/run.out' %(pwd,outdirname)): 
		if len(subprocess.Popen('cat %s/%s/run.out  | grep total' %(pwd,outdirname),shell=True, stdout=subprocess.PIPE).stdout.read().strip()) > 0: 
			isdone=1
os.makedirs('%s/%s' %(outdirname,outdirname))
cmd='cp %s/cryolo/STAR/*.star %s/%s/' %(outdirname,outdirname,outdirname)
subprocess.Popen(cmd,shell=True).wait()
#Loop over all frames
currentframe=2
while currentframe<totframes:
	inlist=glob.glob('%s/cryolo/STAR/*.star'%(outdirname))
	for star in inlist:
		cmd='cp %s %s/%s/%s_1_%i.star' %(star,outdirname,outdirname,star.split('/')[-1][:-10],currentframe)
		subprocess.Popen(cmd,shell=True).wait()
	currentframe=currentframe+1
#Write ctf out file
ctfout=open(ctfoutfile1,'w')
ctfout.write('''# RELION; version 3.0-beta-2

data_

loop_
_rlnMicrographName #1 
_rlnCtfImage #2 
_rlnDefocusU #3 
_rlnDefocusV #4 
_rlnCtfAstigmatism #5 
_rlnDefocusAngle #6 
_rlnVoltage #7 
_rlnSphericalAberration #8 
_rlnAmplitudeContrast #9 
_rlnMagnification #10 
_rlnDetectorPixelSize #11 
_rlnCtfFigureOfMerit #12 
_rlnCtfMaxResolution #13\n''')
for mic in waitinglist:
	ctfline=linecache.getline(mic,6)
	df1=float(ctfline.split()[1])
        df2=float(ctfline.split()[2])
        astig=float(ctfline.split()[3])
        cc=float(ctfline.split()[-2])
        res=float(ctfline.split()[-1])
	ctfout.write('%s/%s.mrc\t%s/%s.ctf:mrc\t%f\t%f\t%f\t%f\t%i\t%f\t0.1\t10000\t%f\t%f\t%f\n'%(outdirname,mic.split('/')[-1][:-9],outdirname,mic.split('/')[-1][:-9],df1,df2,abs(df1-df2),astig,kev,cs,apix,cc,res))
ctfout.close()

extract(outdirname,ctfoutfile1,boxsize,"1_24")

newlist=[]
for movie in glob.glob(indir):
	currentframe=2
	while currentframe<totframes:
		alignedmic=unblur(movie,1,currentframe)
		newlist.append(alignedmic)
		currentframe=currentframe+1

#Wait for unblur to finish
isdone=0
while isdone == 0:
        totalcheck=len(newlist)
        counter=0
        finish_check=0
        while counter < totalcheck:
                if os.path.exists(newlist[counter]):
                        finish_check=finish_check+1
                counter=counter+1

        if finish_check == totalcheck:
                isdone=1

#Extract particles
###Write new ctfout files
ctflist=[]
namelist=[]
currentframe=2
while currentframe<totframes:
	#Symlink mics into dose dir
	micgrouplist=glob.glob('%s/*_1_%i.mrc' %(moviedir,currentframe))
	for mic in micgrouplist: 
		os.symlink('%s/%s' %(pwd,mic),'%s/%s/%s' %(pwd,outdirname,mic.split('/')[-1]))		
	ctfnew='%s_1_%s.star' %(ctfoutfile1[:-5],currentframe)
	ctfwrite=open(ctfnew,'w')
	ctfwrite.write('''# RELION; version 3.0-beta-2

data_

loop_
_rlnMicrographName #1 
_rlnCtfImage #2 
_rlnDefocusU #3 
_rlnDefocusV #4 
_rlnCtfAstigmatism #5 
_rlnDefocusAngle #6 
_rlnVoltage #7 
_rlnSphericalAberration #8 
_rlnAmplitudeContrast #9 
_rlnMagnification #10 
_rlnDetectorPixelSize #11 
_rlnCtfFigureOfMerit #12 
_rlnCtfMaxResolution #13\n''')
	for mic in waitinglist:
        	ctfline=linecache.getline(mic,6)
	        df1=float(ctfline.split()[1])
        	df2=float(ctfline.split()[2])
	        astig=float(ctfline.split()[3])
        	cc=float(ctfline.split()[-2])
	        res=float(ctfline.split()[-1])
        	ctfwrite.write('%s/%s_1_%i.mrc\t%s/%s.ctf:mrc\t%f\t%f\t%f\t%f\t%i\t%f\t0.1\t10000\t%f\t%f\t%f\n'%(outdirname,mic.split('/')[-1][:-14],currentframe,outdirname,mic.split('/')[-1][:-14],df1,df2,abs(df1-df2),astig,kev,cs,apix,cc,res))
	ctfwrite.close()
	namelist.append('1_%s' %(currentframe))
	ctflist.append('%s_1_%s.star' %(ctfoutfile1[:-5],currentframe))
	currentframe=currentframe+1

##Extract
counter=0
while counter < len(ctflist):
	extract(outdirname,ctflist[counter],boxsize,namelist[counter])
	counter=counter+1
print 'finished'



