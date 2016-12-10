-- MySQL dump 10.13  Distrib 5.7.12, for osx10.9 (x86_64)
--
-- Host: localhost    Database: JP_Project
-- ------------------------------------------------------
-- Server version	5.7.15

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Order`
--

DROP TABLE IF EXISTS `Order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Order` (
  `order_id` int(11) NOT NULL AUTO_INCREMENT,
  `totalVolume` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `time` datetime DEFAULT NULL,
  `status` int(11) DEFAULT '0',
  PRIMARY KEY (`order_id`),
  KEY `uid_idx` (`uid`),
  CONSTRAINT `uid` FOREIGN KEY (`uid`) REFERENCES `user` (`uid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=120 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Order`
--

LOCK TABLES `Order` WRITE;
/*!40000 ALTER TABLE `Order` DISABLE KEYS */;
INSERT INTO `Order` VALUES (78,50,1,'2016-09-26 00:52:28',0),(79,15,1,'2016-09-26 00:30:45',0),(80,25,1,'2016-09-26 00:32:56',0),(81,100,1,'2016-09-26 00:34:58',0),(82,120,1,'2016-09-26 00:30:16',0),(83,20,1,'2016-09-26 00:31:24',0),(84,150,1,'2016-09-26 00:33:43',0),(85,100,1,'2016-09-26 00:30:23',0),(86,120,1,'2016-09-26 00:39:50',0),(87,150,1,'2016-09-26 00:54:15',0),(88,100,1,'2016-09-26 00:59:11',0),(89,160,1,'2016-09-26 01:11:45',0),(90,60,1,'2016-09-26 01:15:10',0),(91,500,1,'2016-09-26 01:17:03',0),(98,5000,14,'2016-09-26 00:34:51',0),(99,5000,14,'2016-09-26 00:35:29',0),(100,5000,14,'2016-09-26 00:35:58',0),(101,5000,14,'2016-09-26 00:36:49',0),(102,5000,14,'2016-09-26 00:37:49',0),(103,5000,14,'2016-09-26 00:38:18',0),(104,5000,14,'2016-09-26 00:48:19',0),(105,5000,14,'2016-09-26 00:56:42',0),(106,5000,14,'2016-09-26 00:57:15',0),(107,5000,14,'2016-09-26 00:57:29',0),(108,5000,14,'2016-09-26 01:07:07',0),(109,5000,14,'2016-09-26 01:20:08',0),(110,5000,14,'2016-09-26 00:30:06',0),(111,1000,1,'2016-09-26 00:45:04',0),(112,1000,1,'2016-09-26 00:53:36',0),(113,1500,1,'2016-09-26 00:54:41',0),(114,1500,1,'2016-09-26 01:09:22',NULL),(115,500,1,'2016-09-26 01:10:50',3),(116,5000,5,'2016-09-26 01:13:10',3),(117,1500,5,'2016-09-26 01:13:21',NULL),(118,3000,5,'2016-09-26 01:31:27',NULL),(119,2500,5,'2016-09-26 01:32:34',3);
/*!40000 ALTER TABLE `Order` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-12-09 22:51:33
