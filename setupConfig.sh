# The conditional is only true in production.
if [[ $GOOGLE_APP_CONFIG_DATA != "" ]];
then
    echo $GOOGLE_APP_CONFIG_DATA > $GOOGLE_APPLICATION_CREDENTIALS
fi
