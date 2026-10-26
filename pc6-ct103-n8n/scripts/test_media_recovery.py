import unittest
import media_recovery as m
class Policy(unittest.TestCase):
 def test_repeated_failure_gate(self):
  s={}
  self.assertEqual(m.decide(s,False,True,10000),'observe')
  self.assertEqual(m.decide(s,False,True,10300),'observe')
  self.assertEqual(m.decide(s,False,True,10600),'repair')
 def test_dependency_blocks_even_after_repeated_failure(self):
  s={'failures':9}
  self.assertEqual(m.decide(s,False,False,10000),'blocked')
 def test_cooldown(self):
  self.assertEqual(m.decide({'failures':9,'attempts':[9900]},False,True,10000),'cooldown')
 def test_attempt_cap(self):
  self.assertEqual(m.decide({'failures':9,'attempts':[100,500]},False,True,10000),'max-attempts')
 def test_healthy_resets_failure_but_not_budget(self):
  s={'failures':9,'attempts':[100]}
  self.assertEqual(m.decide(s,True,True,10000),'healthy')
  self.assertEqual(s['failures'],0)
  self.assertEqual(s['attempts'],[100])
 def test_old_attempts_expire(self):
  self.assertEqual(m.decide({'failures':9,'attempts':[1,2]},False,True,100000),'repair')
import tempfile,pathlib,json
from unittest.mock import patch
class IsolatedRuns(unittest.TestCase):
 def test_host_outage_never_reboots(self):
  inventory=[{'vmid':ct,'node':node,'status':'running','name':{200:'ct151-emby',250:'ct162-tunarr',106:'ct106-tunarr'}[ct]} for node,ct,_ in m.SERVICES.values()]
  calls=[]
  def cmd(node,args,timeout=20):
   calls.append(args)
   if args[0]=='pvesh':return json.dumps(inventory)
   raise AssertionError('unexpected command')
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as tmp,patch.object(m,'STATE',pathlib.Path(tmp)),patch.object(m,'host_read',side_effect=RuntimeError('NAS down')),patch.object(m,'command',side_effect=cmd),patch.object(m,'fetch',return_value=b'{}'):
   result={}
   for _ in range(5):result=m.run()
   self.assertFalse(result['actions'])
   self.assertTrue(all(v['decision']=='blocked' for v in result['services'].values()))
   self.assertFalse(any(c[:2]==['pct','reboot'] for c in calls))
 def test_identity_change_never_reboots(self):
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as tmp,patch.object(m,'STATE',pathlib.Path(tmp)),patch.object(m,'host_read',return_value='sample'),patch.object(m,'command',return_value='[]') as c,patch.object(m,'fetch',return_value=b'{}'):
   result={}
   for _ in range(4):result=m.run()
   self.assertFalse(result['actions'])
   self.assertTrue(all(v['decision']=='blocked' for v in result['services'].values()))
   self.assertEqual(c.call_count,4)
 def test_three_failures_reboot_only_target_and_verify(self):
  inventory=[{'vmid':ct,'node':node,'status':'running','name':{200:'ct151-emby',250:'ct162-tunarr',106:'ct106-tunarr'}[ct]} for node,ct,_ in m.SERVICES.values()]
  calls=[];repaired=False
  def cmd(node,args,timeout=20):
   nonlocal repaired
   calls.append((node,args))
   if args[0]=='pvesh':return json.dumps(inventory)
   if args[:2]==['pct','reboot']:repaired=True;return 'ok'
   raise AssertionError(args)
  def guest(name,sample):
   if name=='tunarr-pc9' and not repaired:raise RuntimeError('simulated stale bind')
   return {'bytes':65536}
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as tmp, patch.object(m,'STATE',pathlib.Path(tmp)), patch.object(m,'host_read',return_value='sample.mp4'),patch.object(m,'command',side_effect=cmd),patch.object(m,'guest_probe',side_effect=guest),patch.object(m,'fetch',return_value=b'{}'),patch.object(m.time,'sleep'):
   self.assertFalse(m.run()['actions']);self.assertFalse(m.run()['actions'])
   result=m.run();self.assertTrue(result['ok'])
   self.assertEqual([(n,a) for n,a in calls if a[:2]==['pct','reboot']],[('pc9',['pct','reboot','106'])])
   self.assertEqual(json.loads((pathlib.Path(tmp)/'state.json').read_text())['tunarr-pc9']['attempts'].__len__(),1)
class EmbySafety(unittest.TestCase):
 def test_prolonged_emby_failure_only_observes_and_notifies(self):
  inventory=[{'vmid':ct,'node':node,'status':'running','name':{200:'ct151-emby',250:'ct162-tunarr',106:'ct106-tunarr'}[ct]} for node,ct,_ in m.SERVICES.values()]
  def guest(name,sample):
   if name=='emby':raise RuntimeError('persistent Emby failure')
   return {'bytes':65536}
  def cmd(node,args,timeout=20):
   if args[0]=='pvesh':return json.dumps(inventory)
   self.fail('unexpected command: '+repr(args))
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as tmp,patch.object(m,'STATE',pathlib.Path(tmp)),patch.object(m,'host_read',return_value='sample'),patch.object(m,'guest_probe',side_effect=guest),patch.object(m,'command',side_effect=cmd),patch.object(m,'fetch',return_value=b'{}'):
   for hour in range(72):
    with patch.object(m.time,'time',return_value=100000+hour*3600):result=m.run()
    self.assertEqual(result['services']['emby']['decision'],'observe')
    self.assertFalse(result['actions'])
    self.assertTrue(result['notify'])
   self.assertNotIn('attempts',json.loads((pathlib.Path(tmp)/'state.json').read_text())['emby'])
 def test_reboot_boundary_rejects_non_allowlisted_targets(self):
  with patch.object(m.subprocess,'run') as run:
   for node,ct in [('pc6',200),('pc9',200),('pc6',106),('pc9',250),('other',250)]:
    with self.assertRaises(RuntimeError):m.command(node,['pct','reboot',str(ct)])
   run.assert_not_called()
 def test_reboot_boundary_preserves_allowlisted_targets(self):
  with patch.object(m.subprocess,'run') as run:
   run.return_value.returncode=0;run.return_value.stdout='ok'
   for node,ct in [('pc6',250),('pc9',106)]:self.assertEqual(m.command(node,['pct','reboot',str(ct)]),'ok')
   self.assertEqual(run.call_count,2)
if __name__=='__main__': unittest.main()
