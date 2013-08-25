#!/bin/bash

name="python-wine"
dir="python-wine"


path="$(readlink -f "$(dirname "$0")/../")"
version="$(head "$path/$dir/debian/changelog" -n 1 | cut -d\( -f2 | cut -d\) -f1)"
distros=( $(head "$path/$dir/debian/changelog" -n 1 | cut -d\) -f2 | cut -d\; -f1) )
package_name="$(head "$path/$dir/debian/changelog" -n 1 | cut -d\  -f1)"
package_priority="$(head "$path/$dir/debian/changelog" -n 1 | cut -d\; -f2)"
sourceversion="$(echo $version | cut -d- -f1)"

sourcedir="$name"-"$sourceversion"
sourcetar="$name"_"$sourceversion.orig.tar.gz"

cd "$path"

echo -n "Copying the $name directory to /tmp..."
if [ -d "/tmp/$sourcedir" ]; then
	rm -R "/tmp/$sourcedir"
fi
cp -R "$dir" "/tmp/$sourcedir"
rm -R "/tmp/$sourcedir/.bzr"
echo " done."

cd /tmp

echo -n "Creating TAR.GZ archive of $name version $sourceversion..."
tar --exclude "$sourcedir/.bzr" --exclude "$sourcedir/.bzrignore" --exclude "$sourcedir/debian" -czf "$sourcetar" "$sourcedir"
cp "$sourcetar" "$sourcedir.tar.gz"
echo " done."

echo -n "Signing TAR.GZ archive..."
gpg --armor --yes --sign --detach-sig "$sourcedir.tar.gz"
echo " done."

echo -n "Creating binary package of $name version $version..."
cd "$sourcedir"
debuild -sa > "/tmp/$package_name-$version~${distros[${#distros[@]}-1]}.build-log-binary"
cd ..
echo " done."


# If length of distros is more than one then we have to create a package for
# each distribution, otherwise Launchpad/soyuz won't accept it (though it should >:( )
if [ ${#distros[@]} -gt 1 ]; then
	echo "Package supports more than one distribution, creating multiple source packages..."
	for i in $(seq 0 $((${#distros[@]} - 1))); do
		echo -ne "\t${distros[$i]}..."
		echo "$package_name ($version~${distros[$i]}) ${distros[$i]};$package_priority" > "$sourcedir/debian/changelog"
		tail "$path/$dir/debian/changelog" -n +2 >> "$sourcedir/debian/changelog"
		echo " done."
		echo -n "Creating source package of $name version $version for ${distros[$i]}..."
		cd "$sourcedir"
		debuild -S -sa > "/tmp/$package_name-$version~${distros[$i]}.build-log-source"
		cd ..
		echo " done."
		done
else
	echo -n "Creating source package of $name version $version for ${distros[0]}..."
	cd "$sourcedir"
	debuild -S -sa > "/tmp/$package_name-$version~${distros[$0]}.build-log-source"
	cd ..
	echo " done."
fi