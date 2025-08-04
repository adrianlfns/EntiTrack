rm -r EntiTrack_API/UI
mkdir EntiTrack_API/UI


cd EntiTrack_UI
dotnet publish EntiTrack_UI.csproj -c Release 

cp -r bin/Release/net9.0/publish/wwwroot/* ../EntiTrack_API/UI

cd ..