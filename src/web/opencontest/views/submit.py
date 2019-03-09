# import os


# def addSubmission(probId, lang, code, user, type):
#     sub = Submission()
#     sub.problem = Problem.get(probId)
#     sub.language = lang
#     sub.code = code
#     sub.result = "pending"
#     sub.user = user
#     sub.timestamp = time.time() * 1000
#     sub.type = type
#     if type == "submit":
#         sub.save()
#     else:
#         sub.id = str(uuid4())
#     return sub

# exts = {
#     "c": "c",
#     "cpp": "cpp",
#     "cs": "cs",
#     "java": "java",
#     "python2": "py",
#     "python3": "py",
#     "ruby": "rb",
#     "vb": "vb"
# }

# def readFile(path):
#     try:
#         with open(path, "rb") as f:
#             return f.read().decode("utf-8")
#     except:
#         return None

# def runCode(sub):
#     # Copy the code over to the runner /tmp folder
#     extension = exts[sub.language]
#     os.mkdir(f"/tmp/{sub.id}")
#     with open(f"/tmp/{sub.id}/code.{extension}", "wb") as f:
#         f.write(sub.code.encode("utf-8"))
    
#     prob = sub.problem
#     tests = prob.samples if sub.type == "test" else prob.tests
    
#     # Copy the input over to the tmp folder for the runner
#     for i in range(tests):
#         shutil.copyfile(f"/db/problems/{prob.id}/input/in{i}.txt", f"/tmp/{sub.id}/in{i}.txt")

#     # Output files will go here
#     os.mkdir(f"/tmp/{sub.id}/out")

#     # Run the runner
#     if os.system(f"docker run --network=none -m 256MB -v /tmp/{sub.id}/:/source nathantheinventor/open-contest-dev-{sub.language}-runner {tests} 5 > /tmp/{sub.id}/result.txt") != 0:
#         raise Exception("Something went wrong")

#     inputs = []
#     outputs = []
#     answers = []
#     errors = []
#     results = []
#     result = "ok"

#     for i in range(tests):
#         inputs.append(sub.problem.testData[i].input)
#         errors.append(readFile(f"/tmp/{sub.id}/out/err{i}.txt"))
#         outputs.append(readFile(f"/tmp/{sub.id}/out/out{i}.txt"))
#         answers.append(sub.problem.testData[i].output)
        
#         res = readFile(f"/tmp/{sub.id}/out/result{i}.txt")
#         if res == "ok" and answers[-1].strip() != outputs[-1].strip():
#             res = "wrong_answer"
#         if res == None:
#             res = "tle"
#         results.append(res)

#         # Make result the first incorrect result
#         if res != "ok" and result == "ok":
#             result = res

#     sub.result = result
#     if readFile(f"/tmp/{sub.id}/result.txt") == "compile_error\n":
#         sub.result = "compile_error"
#         sub.delete()
#         sub.compile = readFile(f"/tmp/{sub.id}/out/compile_error.txt")
#         return

#     sub.results = results
#     sub.inputs = inputs
#     sub.outputs = outputs
#     sub.answers = answers
#     sub.errors = errors

#     if sub.type == "submit":
#         sub.save()

#     shutil.rmtree(f"/tmp/{sub.id}", ignore_errors=True)

# def submit(params, setHeader, user):
#     probId = params["problem"]
#     lang   = params["language"]
#     code   = params["code"]
#     type   = params["type"]
#     submission = addSubmission(probId, lang, code, user, type)
#     runCode(submission)
#     return submission.toJSON()

# def changeResult(params, setHeader, user):
#     id = params["id"]
#     sub = Submission.get(id)
#     if not sub:
#         return "Error: incorrect id"
#     sub.result = params["result"]
#     sub.save()
#     return "ok"

# def rejudge(params, setHeader, user):
#     id = params["id"]
#     submission = Submission.get(id)
#     runCode(submission)
#     return submission.result

# register.post("/submit", "loggedin", submit)
# register.post("/changeResult", "admin", changeResult)
# register.post("/rejudge", "admin", rejudge)

from uuid import uuid4
import os

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotFound, HttpResponse

from opencontest.views.general import get_person
from opencontest.models import Problem, Contest, Submission, Result

exts = {
    "c": "c",
    "cpp": "cpp",
    "cs": "cs",
    "java": "java",
    "python2": "py",
    "python3": "py",
    "ruby": "rb",
    "vb": "vb"
}

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def submit(req):
    # 1. Check that the contest is correct
    contest = Contest.current()
    person = get_person(req)
    prob_id = req.POST["problem"]
    prob = Problem.objects.get(id=prob_id)
    if (contest is None or prob.contest != contest) and not person.is_admin:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    # 2. Get the other parameters
    lang = req.POST["language"]
    code = req.POST["code"]
    type = req.POST["type"]

    # 3. Create the submission DB record
    sub = Submission()
    sub.problem = prob
    sub.is_full = type == "submit"
    sub.contest = contest
    sub.timestamp = timezone.now()
    sub.person = person
    sub.code_path = f"/code/{uuid4()}.{exts[lang]}"
    sub.result = Result.objects.get(name="Pending")
    sub.save()

    return HttpResponse("")