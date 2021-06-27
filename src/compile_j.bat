@echo off

if "%1"=="" (
  echo Usage %~nx0 ^<filename^>
  exit
)

rem set JAVA_HOME=C:\Program Files\Java\jdk1.7.0_11
rem set JAVA_HOME=C:\Program Files\Java\jdk1.6.0_11
set JAVA_HOME=C:\Program Files\Java\jdk-11.0.11


set JAVAC="%JAVA_HOME%\bin\javac.exe"
set JAVAP="%JAVA_HOME%\bin\javap.exe"
set JASPER="%JAVA_HOME%\bin\java.exe" -jar "%~dp0\jasper\jasper.jar"
set JASMIN="%JAVA_HOME%\bin\java.exe" -jar "%~dp0\jasmin-2.4\jasmin.jar"



set FILENAME=%~n1
%JASMIN% %FILENAME%.j
