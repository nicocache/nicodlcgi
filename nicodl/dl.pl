#!/usr/bin/perl
use utf8;
use File::Spec;
use strict;
use Digest::MD5 qw/md5_hex/;
use File::MimeInfo qw(globs);
use File::Basename 'basename', 'dirname';
use CGI;
use CGI::Cookie;

use Net::Netrc;
use WWW::NicoVideo::Download;
use LWP::UserAgent;
use Web::Scraper;
use XML::Simple;

require DBD::SQLite;
require DBI;

require File::Spec->catfile(dirname(__FILE__),"../login/common.pl");
require File::Spec->catfile(dirname(__FILE__),"common_ndl.pl");

my $mach = Net::Netrc->lookup('nicovideo');
my ($nicologin, $nicopassword, $nicoaccount) = $mach->lpa;

my $client = WWW::NicoVideo::Download->new(
    email => $nicologin,
    password => $nicopassword,
);

my %conf=GetConf(File::Spec->catfile(dirname(__FILE__),"dl.conf"));
my $homeDir=$conf{"dlhome"};

my $dbh = GetDatabaseHandleNicodl();
my $sth=$dbh->prepare("select * from download");
$sth->execute;

my $ua = LWP::UserAgent->new();

my $dbhId=GetDatabaseHandle();

while(my $hash=$sth->fetchrow_hashref()){
  my $userHash=GetAccountFromId($dbhId,$hash->{"owner"});
  my $userName=$userHash->{"login"};
  if($hash->{"kind"} eq "video"){
    my $video_id=$hash->{"url"};
    print "Downloading: $video_id\n";
    DownloadNicovideo($video_id,$homeDir,$userName,"independent",$client,$hash,"");
  }elsif($hash->{"kind"} eq "mylist"){
    my $res= $ua->get("http://www.nicovideo.jp/mylist/".$hash->{"url"});
    my @videos;
    my $resText=$res->content;
    $resText=~ s/"watch_id"\s*:\s*"(\w+)"/push(@videos,$1)/ge;
    my $cnt=0;
    print "DL Group:$hash->{'url'}\n";
    foreach my $urlInMl (@videos){
      DownloadNicovideo($urlInMl,$homeDir,$userName,$hash->{"url"},$client,$hash,"http://www.nicovideo.jp/mylist/".$hash->{"url"});
      $cnt++;
#      last if $cnt>$hash->{""};
    }
  }
}

sub DownloadNicovideo{
  my $ua = LWP::UserAgent->new();
  my ($video_id,$dlDir,$userName,$dirName,$client,$hash,$url)=@_;
  my $res = $ua->get("http://ext.nicovideo.jp/api/getthumbinfo/$video_id");
  my $ext = XMLin($res->content)->{thumb}{movie_type};
  my $title = XMLin($res->content)->{thumb}{title};
  $title=~ s/[\/\\\:\,\;\*\?\"\<\>\|]//g;
  $userName=~ s/[\/\\\:\,\;\*\?\"\<\>\|]//g;

  my $userDir=File::Spec->catfile($dlDir , $userName);
  mkdir $userDir or die "$!:$userDir" if ! -d $userDir;

  my $workDir=File::Spec->catfile($userDir,$dirName);
  mkdir $workDir or die "$!:$workDir" if ! -d $workDir;

  my $filetmp=File::Spec->catfile($workDir ,"tmp.$ext");
  my $file=File::Spec->catfile($workDir , "$video_id.$title.$ext");
  if(-e $file){
    my $sth=$dbh->prepare("select * from movie where path = '".escape_sql($file)."'");
    $sth->execute();
    if(! $sth->fetchrow_hashref()){
      RegisterNicovideo($dbh,$dirName,$hash,$url,$title,$file,$video_id);
    }
    return;
  }
  print "Downloading: $file\n";
  unlink $filetmp if -e $filetmp;
  open my $fh, '>', $filetmp or die $!;
  eval{
    my $vurl= $client->prepare_download($video_id);
    if ($vurl=~ /low$/){die "low quality";}
    $client->download($video_id, sub {
      my ($data, $res, $proto) = @_;
      print {$fh} $data;
      });
    rename $filetmp,$file;
  };
  sleep 10;
  if ($@) {
    warn "ERROR: $@\n";
    unlink $filetmp;
    return;
  }
  RegisterNicovideo($dbh,$dirName,$hash,$url,$title,$file,$video_id);
}

sub RegisterNicovideo{
  my ($dbh,$dirName,$hash,$url,$title,$file,$watch_id)=@_;
  my $sth=$dbh->prepare("select * from collection where url = '$url' and owner = $hash->{'owner'} and public = ".ParseInt($hash->{'pubic'}));
  $sth->execute;
  my $groupId=0;
  if(my $hash2=$sth->fetchrow_hashref()){
    $groupId=$hash2->{"id"};
  }else{
    $dbh->do("insert into collection(id,owner,public,title,url) select case when max(id) is null then 1 else max(id) +1 end,$hash->{'owner'},".ParseInt($hash->{'pubic'}).",'$dirName','$url' from collection;");
    my $sth2=$dbh->prepare("select * from collection where url = $dirName");
    $sth2->execute;
    my $hash2=$sth2->fetchrow_hashref();
    $groupId=$hash2->{"id"};
  }
  $dbh->do("insert into movie(id,owner,public,title,path,group_id,watch_id) select case when max(id) is null then 1 else max(id) +1 end,$hash->{'owner'},".ParseInt($hash->{'pubic'}).",'".escape_sql($title)."','".escape_sql($file)."',$groupId,'$watch_id' from movie;");
}
