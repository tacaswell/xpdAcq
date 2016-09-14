import unittest
import os
import shutil
import yaml
from time import strftime

# FIXME
from xpdacq.glbl import glbl
from xpdacq.beamtime import Beamtime
import xpdacq.beamtimeSetup as bts
from xpdacq.beamtimeSetup import (_start_beamtime, _end_beamtime,
                                  _delete_home_dir_tree, _make_clean_env,
                                  _clean_info, _load_bt, _load_bt_info,
                                  _tar_user_data)
from xpdacq.utils import (export_userScriptsEtc, import_userScriptsEtc,
                          import_sample)


class NewBeamtimeTest(unittest.TestCase):
    def setUp(self):
        self.base_dir = glbl.base
        self.home_dir = os.path.join(self.base_dir, 'xpdUser')
        self.config_dir = os.path.join(self.base_dir, 'xpdConfig')
        self.PI_name = 'Billinge '
        self.saf_num = '123'  # must be 123 for proper load of config yaml => don't change
        self.wavelength = 0.1812
        self.experimenters = [('van der Banerjee', 'S0ham', 1),
                              ('Terban ', ' Max', 2)]

    def tearDown(self):
        os.chdir(self.base_dir)
        if os.path.isdir(self.home_dir):
            shutil.rmtree(self.home_dir)
        if os.path.isdir(os.path.join(self.base_dir, 'xpdConfig')):
            shutil.rmtree(os.path.join(self.base_dir, 'xpdConfig'))
        if os.path.isdir(os.path.join(self.base_dir, 'pe2_data')):
            shutil.rmtree(os.path.join(self.base_dir, 'pe2_data'))
        if os.path.isdir(glbl.archive_dir):
            shutil.rmtree(glbl.archive_dir)

    def test_make_clean_env(self):
        # check directory structure from glbl
        home_dir = os.path.join(self.base_dir, 'xpdUser')
        conf_dir = os.path.join(self.base_dir, 'xpdConfig')
        tiff_dir = os.path.join(self.home_dir, 'tiff_base')
        usrconfig_dir = os.path.join(self.home_dir, 'config_base')
        import_dir = os.path.join(self.home_dir, 'Import')
        userysis_dir = os.path.join(self.home_dir, 'userAnalysis')
        userscripts_dir = os.path.join(self.home_dir, 'userScripts')
        yml_dir = os.path.join(self.home_dir, usrconfig_dir, 'yml')
        sample_dir = os.path.join(yml_dir, 'samples')
        experiment_dir = os.path.join(yml_dir, 'experiments')
        scanplan_dir = os.path.join(yml_dir, 'scanplans')
        dirs = _make_clean_env()
        dir_list = [home_dir, conf_dir, tiff_dir, usrconfig_dir,
                    import_dir, userysis_dir, userscripts_dir,
                    yml_dir, sample_dir, experiment_dir, scanplan_dir]
        for el in dir_list:
            self.assertTrue(el in glbl.allfolders)

    def test_start_beamtime(self):
        # sanity check. xpdUser directory exists.
        # First make sure the code works right when it doesn't exist.
        self.assertFalse(os.path.isdir(self.home_dir))
        self.assertRaises(RuntimeError,
                          lambda: _start_beamtime(self.PI_name, self.saf_num))
        # now make it the proper thing...xpdUser directory
        os.mkdir(self.home_dir)
        self.assertTrue(os.path.isdir(self.home_dir))
        # but put a file in it
        self.newfile = os.path.join(self.home_dir, 'touched.txt')
        open(self.newfile, 'a').close()
        self.assertTrue(os.path.isfile(self.newfile))
        self.assertRaises(FileExistsError,
                          lambda: _start_beamtime(self.PI_name, self.saf_num))
        os.remove(self.newfile)
        # do the same but with directories
        self.newdir = os.path.join(self.home_dir, 'userJunk')
        os.mkdir(self.newdir)
        self.assertTrue(os.path.isdir(self.newdir))
        self.assertRaises(FileExistsError,
                          lambda: _start_beamtime(self.PI_name, self.saf_num))
        os.removedirs(self.newdir)
        # real doing: 
        os.mkdir(self.home_dir)
        self.assertTrue(os.path.isdir(self.home_dir))
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        self.assertIsInstance(self.bt, Beamtime)
        # test normalized md
        self.assertEqual('Billinge', self.bt.get('bt_piLast'))
        self.assertEqual('123', self.bt.get('bt_safN'))
        self.assertEqual(self.experimenters, self.bt.get('bt_experimenters'))
        self.assertEqual(self.wavelength, self.bt.get('bt_wavelength'))
        self.assertEqual(os.getcwd(), self.home_dir)
        # FIXME
        # strtScnLst = ['bt_bt.yml','ex_l-user.yml','sa_l-user.yml','sp_ct_0.1.yml','sp_ct_0.5.yml','sp_ct_1.yml','sp_ct_5.yml','sp_ct_10.yml','sp_ct_30.yml']
        # self.assertEqual(newobjlist,strtScnLst)

    def test_end_beamtime(self):
        _required_info = ['bt_piLast', 'bt_safN', 'bt_uid']
        # end_beamtime has been run
        self.assertRaises(FileNotFoundError, lambda: _end_beamtime())
        # entire trip. _start_beamtime to _end_beamtime
        self.bt = _start_beamtime(self.PI_name, self.saf_num,
                                  self.experimenters,
                                  wavelength=self.wavelength)
        bt_path_src = os.path.join(glbl.yaml_dir, 'bt_bt.yml')
        bt_path_dst = os.path.join(glbl.import_dir, 'bt_bt.yml')
        # move out for now, no bt
        shutil.move(bt_path_src, bt_path_dst)
        self.assertTrue(os.path.isfile(bt_path_dst))
        self.assertFalse(os.path.isfile(bt_path_src))
        self.assertRaises(SystemExit, lambda: _load_bt(glbl.yaml_dir))
        # move back and test archieving funtionality
        shutil.move(bt_path_dst, bt_path_src)
        self.assertTrue(os.path.isfile(bt_path_src))
        self.assertFalse(os.path.isfile(bt_path_dst))
        pi_name = self.bt.get('bt_piLast')
        saf_num = self.bt.get('bt_safN')
        bt_uid = self.bt.get('bt_uid')
        archive_name = _load_bt_info(self.bt, _required_info)
        archive_full_name = _tar_user_data(archive_name)
        test_tar_name = '_'.join([pi_name, saf_num, bt_uid,
                                  strftime('%Y-%m-%d-%H%M')])
        # is tar file name correct? 
        self.assertEqual(archive_full_name,
                         os.path.join(glbl.archive_dir, test_tar_name))
        # are contents tared correctly?
        archive_test_dir = os.path.join(glbl.home, 'tar_test')
        os.makedirs(archive_test_dir, exist_ok=True)
        shutil.unpack_archive(archive_full_name + '.tar', archive_test_dir)
        content_list = os.listdir(archive_test_dir)
        # is tarball starting from xpdUser?
        self.assertTrue('xpdUser' in content_list)
        # is every directory included
        basename_list = list(map(os.path.basename, glbl.allfolders))
        _exclude_list = ['xpdUser', 'xpdConfig', 'yml', 'samples',
                         'scanplans', 'experiments']
        # _exclude_list means sub directories and top directories 
        # that will not be in tar structure
        for el in _exclude_list:
            basename_list.remove(el)
        for el in basename_list:
            self.assertTrue(el in os.listdir(os.path.join(archive_test_dir,
                                                          'xpdUser')))
        # now test deleting directories
        _delete_home_dir_tree()
        self.assertTrue(len(os.listdir(glbl.home)) == 0)

    def test_import_userScript_Etc(self):
        src = glbl.import_dir
        dst = [glbl.yaml_dir, glbl.usrScript_dir]
        os.makedirs(src, exist_ok=True)
        for el in dst:
            os.makedirs(el, exist_ok=True)
        self.assertTrue(os.path.isdir(glbl.config_base))
        self.assertTrue(os.path.isdir(glbl.yaml_dir))
        self.assertTrue(os.path.isdir(glbl.usrScript_dir))
        # case1 : no files in import_dir, should return nothing
        self.assertEqual(import_userScriptsEtc(), None)
        # case2 : a tar file with three kind of files, test if it is successfully moved and unpacked
        yaml_name = 'touched.yml'
        py_name = 'touched.py'
        npy_name = 'mask.npy'
        exception_name = 'yaml.pdf'
        untared_list = [yaml_name, py_name, npy_name, exception_name]
        tar_yaml_name = 'tar.yml'
        tar_py_name = 'tar.py'
        tar_npy_name = 'tar.npy'
        tared_list = [tar_yaml_name, tar_py_name, tar_npy_name]
        # create archive file
        for el in tared_list:
            f_path = os.path.join(src, el)
            open(f_path, 'a').close()
        cwd = os.getcwd()
        os.chdir(src)  # inevitable step for compression
        tar_name = 'HappyMeal'
        shutil.make_archive(tar_name,
                            'tar')  # now data should be in xpdUser/Import/
        full_tar_name = os.path.join(src, tar_name + '.tar')
        os.chdir(cwd)
        moved_list_1 = import_userScriptsEtc()
        for el in tared_list:
            self.assertTrue(el in list(map(lambda x: os.path.basename(x),
                                           moved_list_1)))
        # is tar file still there?
        self.assertTrue(os.path.isfile(full_tar_name))
        # case 3 : tared file, individual files and unexcepted file/dir appear in Import/
        for el in untared_list:
            f_path = os.path.join(src, el)
            open(f_path, 'a').close()
        exception_dir_name = os.path.join(src, 'touched')
        os.makedirs(exception_dir_name, exist_ok=True)
        moved_list_2 = import_userScriptsEtc()
        # grouping file list
        final_list = list(tared_list)
        final_list.extend(untared_list)
        final_list.remove(exception_name)
        for el in final_list:
            self.assertTrue(el in list(map(lambda x: os.path.basename(x),
                                           moved_list_2)))
        # is tar file still there?
        self.assertTrue(os.path.isfile(full_tar_name))
        # is .pdf file still there?
        self.assertTrue(os.path.isfile(os.path.join(src, exception_name)))
        # is directory still there?
        self.assertTrue(os.path.isdir(exception_dir_name))

    def test_export_userScriptsEtc(self):
        os.makedirs(glbl.usrScript_dir, exist_ok=True)
        os.makedirs(glbl.yaml_dir, exist_ok=True)
        new_script = os.path.join(glbl.usrScript_dir, 'script.py')
        open(new_script, 'a').close()
        new_yaml = os.path.join(glbl.yaml_dir, 'touched.yml')
        open(new_yaml, 'a').close()
        tar_f_path = export_userScriptsEtc()
        shutil.unpack_archive(tar_f_path, glbl.home)

        userScript_dir_tail = os.path.split(glbl.usrScript_dir)[1]
        config_base_tail = os.path.split(glbl.config_base)[1]
        yaml_dir_tail = os.path.split(glbl.yaml_dir)[1]
        # are parent dirs in xpdUser?
        self.assertTrue(os.path.isdir(os.path.join(glbl.home,
                                                   userScript_dir_tail)))
        self.assertTrue(os.path.isdir(os.path.join(glbl.home,
                                                   config_base_tail)))
        # are files in unpacked dirs?
        self.assertTrue('script.py' in os.listdir(os.path.join(glbl.home,
                                                               userScript_dir_tail)))
        self.assertTrue('touched.yml' in os.listdir(
            os.path.join(glbl.home, config_base_tail, yaml_dir_tail)))
