from django.shortcuts import render, render_to_response
from video.models import *
from blog.models import Post
from qa.models import Question as qaQuestion
from video.forms import VideoCommentForm
from main.models import UserProfile, UserActivityLog, view_page
from django.contrib.auth.decorators import login_required
from quiz.models import Question, Answer, QuestionResponse
from django.http import HttpResponseRedirect
from random import shuffle

# Create your views here.

@login_required
def home(request):
	view_page(request.user, UserActivityLog.HOME)
	params = {
		'videos': Video.objects.all()[:5],
		'blogs': Post.objects.all().order_by('-created')[:5],
		'questions': qaQuestion.objects.all()[:5]
	}
	return render(request, 'main/home.html', params)

@login_required
def topicList(request):
	view_page(request.user, UserActivityLog.TOPICS)	

	allTopics = Topic.objects.all().order_by('grade').order_by('order_value')
	topicsWithVideos = []
	for topic in allTopics:
		if len(Video.objects.filter(topic=topic)) > 0:
			topicsWithVideos.append(topic)
	return render(request, 'main/topics.html', {'topics': topicsWithVideos})

@login_required
def getVideos(request, topicName):
	view_page(request.user, UserActivityLog.VIDEOS)	

	params = {
		'videos': Video.objects.filter(topic=Topic.objects.get(name=topicName)),
		'topic': topicName,
	}
        return render(request, 'main/videos.html', params)

@login_required
def getVideo(request, vidNumber):
	view_page(request.user, UserActivityLog.VIDEO, vidNumber)	

	video = Video.objects.get(id=vidNumber)
	viewed_count = UserActivityLog.objects.filter(id_viewed=vidNumber).count()

	if request.method == 'POST':
		form = VideoCommentForm(request.POST)
		if form.is_valid():
			newComment = VideoComment()
			newComment.poster = request.user
			newComment.post = video
			newComment.body = form.cleaned_data['body']
			newComment.save()
		form = VideoCommentForm()
	else:
		form = VideoCommentForm()
		
	args = {
		'video': video,
		'comments': VideoComment.objects.filter(post=video),
		'myform': form,
		'viewCount': viewed_count,
	}
        return render(request, 'main/video.html', args)

@login_required
def getVideoQuiz(request, vidNumber):
	""" Renders a view.
	Ouput Parameters:
		@questionDict: A Dictionary of Questions to sets of Answers
		that belong to that question
	"""
	view_page(request.user, UserActivityLog.QUIZ, vidNumber)	

	currentUser = UserProfile.objects.get(user=request.user)
	video = Video.objects.get(id=vidNumber)
	questions = Question.objects.filter(video_ref=video)
	questionDict = {}
	for question in questions:
		hasBeenAnswered = False
		isCorrect = False
		responsesFromUser = QuestionResponse.objects.filter(user=currentUser)
		if responsesFromUser:
			responsesForThisQuestion = responsesFromUser.filter(question=question)
			if len(responsesForThisQuestion) == 1:
				hasBeenAnswered = True
				isCorrect = responsesForThisQuestion[0].correct
			elif len(responsesForThisQuestion) > 1:
				# Shouldn't ever reach here. This means this user
				# has answered this question multiple times
				hasBeenAnswered = True
				isCorrect = False

		answers_for_question = []
		answer_query_set = Answer.objects.filter(question_ref=question)
		for answer in answer_query_set:
			answers_for_question.append(answer)
		shuffle(answers_for_question)
		questionDict[question] = [answers_for_question, hasBeenAnswered, isCorrect]
		#questionDict[question] = answers_for_question
	args = {
		'questionDict': questionDict,
		'questionCount': len(questionDict),
		'vidNumber': vidNumber,
		'vidTopic': video.topic,
	}
	return render(request, 'quiz/questions.html', args)

@login_required
def returnToPrevPage(request):
	"""
		Simply returns back to previous page
	"""
	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
