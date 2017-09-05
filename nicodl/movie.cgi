#!/usr/bin/perl
use File::Spec;
use strict;
use Digest::MD5 qw/md5_hex/;
use File::MimeInfo qw(globs);
use File::Basename 'basename', 'dirname';
use CGI;
use CGI::Cookie;

require DBD::SQLite;
require DBI;

require File::Spec->catfile(dirname(__FILE__),"../login/common.pl");

my $dbhId=GetDatabaseHandle();
my $q = new CGI;

my $hash= $q->cookie("login_session");
my $sessionHash= GetSessionData($dbhId,$hash);

my %conf=GetConf(File::Spec->catfile(dirname(__FILE__),"dl.conf"));

my $dbh = DBI->connect("dbi:SQLite:dbname=".$conf{"sqlitedb"});

my @pathInfo = split("/", substr($q->path_info(),1));

if(@pathInfo==0 || $pathInfo[0] eq ""){exit;}

my $sth=$dbh->prepare("select * from movie where watch_id = '$pathInfo[0]'");
$sth->execute;

if(my $info=$sth->fetchrow_hashref()){
  if($info->{"public"} || ($sessionHash && $info->{"owner"} == $sessionHash->{"id"})){
    TransferFile($info->{"path"});
    exit;
  }else{
    print "Status: 401 Unauthorized\n\n"
  }
}
else{
  print "Status: 404 Not Found\n\n";
}

sub TransferFile{
  my $file=$_[0];
  my ($ext)= $file =~ m!\.([^\.]+)$!;

  my $blocksize=4096;

  my $mimetype=globs($file);
  my $filesize=-s $file;

  open MOVIE, "<" , $file or die;
  binmode MOVIE;

  my $range=$ENV{'HTTP_RANGE'};
print <<"HEAD";
Content-type: $mimetype
Accept-Ranges: bytes
HEAD
print "Etag: \"". md5_hex($ENV{"REQUEST_URI"}) ."$filesize\"\n";

  if($range ne ""){
    my ($start,$end)= $range=~ m/(\d*)\-(\d*)/;
    if ($start eq "" || $start>$filesize){$start=0;}
    if ($end eq "" || $end<=$start){$end=$filesize-1;}
    my $length=$end-$start+1;

print <<"HEAD";
Status: 206 Partial Content
Content-Length: $length
Content-Range: bytes $start-$end/$filesize

HEAD

    binmode STDOUT;
    seek MOVIE, $start,0;
    my $current=$start;

    while (read MOVIE, my $buffer, ($end-$current+1<$blocksize?$end-$current+1:$blocksize)){
      print $buffer;
      $current+=$blocksize;
      if($end<=$current){return;}
    }
  }else{
    print "Content-Length: $filesize\n\n";
    binmode STDOUT;

    while (read MOVIE, my $buffer, $blocksize){
      print $buffer;
    }
  }
}

sub GetConf{
  my $file=$_[0];
  open(CONF,"< $file");
  my %result;
  while(my $line=<CONF>){
    if($line =~ m/^\#/){ next;}
    if($line =~ m/^(\w+)\=(.+)$/){
      $result{$1}=$2;
      next;
    }
  }
  return %result;
}
